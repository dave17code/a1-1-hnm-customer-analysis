"""A1-1: 고객 단위 표본을 분석하는 재사용 가능한 파이프라인.

분석 라이브러리는 NumPy와 Pandas만 사용합니다. 차트는 노트북에서 작성합니다.
"""
from pathlib import Path
import json
import tempfile

import numpy as np
import pandas as pd


class DataAnalyzer:
    SEGMENTS = ["VIP", "Loyal", "RecentLowFreq", "AtRisk", "Regular"]

    def __init__(self, data_path=None):
        # 기본 입력은 src의 상위, 즉 CSV 3개와 NPZ·JSON이 있는 프로젝트 최상위입니다.
        self.data_path = (Path(data_path).expanduser().resolve() if data_path is not None
                          else Path(__file__).resolve().parents[1])
        self.df = None
        self.customers = None
        self.articles = None
        self.image_features = None
        self.rfm = None
        self.audit = []
        self.outlier_report = None

    def load_data(self):
        """원본 표본을 로드하고 many-to-one 조인으로 거래 행 수를 보존합니다."""
        p = self.data_path
        required = ["transactions.csv", "customers.csv", "articles.csv",
                    "images.npz", "provenance.json"]
        missing = [name for name in required if not (p / name).is_file()]
        if missing:
            raise FileNotFoundError(f"데이터 폴더 {p}에 필요한 파일이 없습니다: {missing}")
        self.meta = json.loads((p / "provenance.json").read_text(encoding="utf-8"))
        tx = pd.read_csv(p / "transactions.csv", dtype={
            "customer_id": str, "article_id": str, "sales_channel_id": str})
        self.articles = pd.read_csv(p / "articles.csv", dtype=str,
                                    keep_default_na=False).replace("", np.nan)
        self.customers = pd.read_csv(p / "customers.csv", dtype=str,
                                     keep_default_na=False).replace("", np.nan)
        tx = tx.rename(columns={"t_dat": "order_date"})
        tx["order_date"] = pd.to_datetime(tx["order_date"], format="%Y-%m-%d")
        tx["price"] = pd.to_numeric(tx["price"], errors="raise")
        if tx[["customer_id", "article_id", "order_date", "price"]].isna().any().any():
            raise ValueError("거래의 필수 값이 누락되었습니다. 원본을 확인하세요.")
        if not np.isfinite(tx.price).all() or (tx.price < 0).any():
            raise ValueError("음수 또는 비유한 가격이 있습니다. 거래 의미를 먼저 확인하세요.")
        # 원본 거래행의 price를 분석용 거래금액으로 대응시킵니다.
        # 수량이나 주문 총액을 추정하지 않으며 원본 price는 그대로 보존합니다.
        tx["amount"] = tx["price"]
        if self.articles.article_id.duplicated().any() or self.customers.customer_id.duplicated().any():
            raise ValueError("상품/고객 테이블의 ID가 중복됩니다.")
        if not tx.article_id.isin(self.articles.article_id).all():
            raise ValueError("상품 CSV에 없는 거래 상품 ID가 있습니다.")
        if not tx.customer_id.isin(self.customers.customer_id).all():
            raise ValueError("고객 CSV에 없는 거래 고객 ID가 있습니다.")
        self.customers["age"] = pd.to_numeric(self.customers.age, errors="raise")
        self.df = tx.merge(self.articles, on="article_id", how="left", validate="many_to_one")
        self.df = self.df.merge(self.customers, on="customer_id", how="left", validate="many_to_one")
        for col in ["sales_channel_id", "product_type_name", "product_group_name", "colour_group_name"]:
            self.df[col] = self.df[col].astype("category")
        with np.load(p / "images.npz", allow_pickle=False) as images:
            self.image_ids = images["article_ids"].astype(str)
            self.pixels = images["pixels"]
        if self.pixels.ndim != 4 or self.pixels.shape[-1] != 3 or self.pixels.dtype != np.uint8:
            raise ValueError("이미지는 (N, H, W, 3)의 uint8 RGB 배열이어야 합니다.")
        if len(self.image_ids) != len(self.pixels) or len(np.unique(self.image_ids)) != len(self.image_ids):
            raise ValueError("이미지 ID와 배열의 대응이 잘못되었습니다.")
        if not pd.Series(self.image_ids).isin(self.articles.article_id).all():
            raise ValueError("상품 표본에 속하지 않는 이미지가 있습니다.")
        self.audit = []
        self.rfm = None
        self.outlier_report = None
        self.image_features = None
        return self.df

    def handle_missing_values(self, strategy="group_median", group_col="club_member_status", column="age"):
        """고객별 한 행에서 그룹 통계를 계산해 구매 빈도에 의한 가중을 방지합니다."""
        if strategy not in {"group_median", "group_mean"}:
            raise ValueError("strategy는 group_median 또는 group_mean입니다.")
        customers = self.customers.copy()
        missing_group = int(customers[group_col].isna().sum())
        customers[group_col] = customers[group_col].fillna("Unknown")
        values = pd.to_numeric(customers[column], errors="raise")
        before = int(values.isna().sum())
        agg = "median" if strategy == "group_median" else "mean"
        group_values = customers.groupby(group_col, dropna=False)[column].transform(agg)
        fallback = getattr(values, agg)()
        if pd.isna(fallback):
            raise ValueError("표본에 관측된 나이가 없어 대치할 수 없습니다.")
        fallback_n = int((values.isna() & group_values.isna()).sum())
        customers[column] = values.fillna(group_values).fillna(fallback)
        self.customers = customers
        lookup = customers.set_index("customer_id")
        self.df[column] = self.df.customer_id.map(lookup[column])
        self.df[group_col] = self.df.customer_id.map(lookup[group_col]).astype("category")
        self.audit.extend([
            {"target": "customer." + group_col, "checked": len(customers), "before_missing": missing_group,
             "after_missing": 0, "action": "Unknown으로 표시"},
            {"target": "customer." + column, "checked": len(customers), "before_missing": before,
             "after_missing": int(customers[column].isna().sum()),
             "action": f"{strategy}; 전체 통계 대체 {fallback_n}명"},
        ])
        return self.df

    def engineer_features(self):
        """이미지별 픽셀 통계는 for/apply 없이 배열의 축을 한 번에 축약합니다."""
        self.image_features = pd.DataFrame({
            "article_id": self.image_ids,
            "image_mean": self.pixels.mean(axis=(1, 2, 3)),
            "image_std": self.pixels.std(axis=(1, 2, 3), ddof=0),
        })
        self.df = self.df.drop(columns=["image_mean", "image_std", "image_missing"], errors="ignore")
        self.df = self.df.merge(self.image_features, on="article_id", how="left", validate="many_to_one")
        self.df["image_missing"] = self.df.image_mean.isna()
        # 상품명 결측치를 길이 0인 실제 상품명으로 오해하지 않도록 nullable 정수로 유지합니다.
        self.df["name_length"] = self.df.prod_name.astype("string").str.len()
        missing = int((~self.articles.article_id.isin(self.image_ids)).sum())
        self.audit.append({"target": "product.image", "checked": len(self.articles),
                           "before_missing": missing, "after_missing": missing,
                           "action": "이미지 특성만 결측으로 유지; 거래는 보존"})
        return self.df

    def detect_outliers(self, column="price", threshold=1.5, treatment="clip"):
        """Q1-k*IQR, Q3+k*IQR를 직접 계산합니다. 원본 컬럼은 보존합니다."""
        if not np.isfinite(threshold) or threshold < 0:
            raise ValueError("threshold는 0 이상의 유한한 값이어야 합니다.")
        if treatment not in {"clip", "flag"}:
            raise ValueError("treatment는 clip 또는 flag입니다.")
        values = self.df[column]
        q1, q3 = values.quantile([0.25, 0.75])
        iqr = q3 - q1
        lower, upper = q1 - threshold * iqr, q3 + threshold * iqr
        mask = (values < lower) | (values > upper)
        self.df[column + "_outlier"] = mask
        if treatment == "clip":
            self.df[column + "_iqr"] = values.clip(lower=lower, upper=upper)
        self.outlier_report = {"column": column, "threshold": threshold, "q1": float(q1),
                               "q3": float(q3), "iqr": float(iqr), "lower": float(lower),
                               "upper": float(upper), "count": int(mask.sum()),
                               "rate": float(mask.mean())}
        return self.df.loc[mask].copy()

    def calculate_rfm(self, customer_col="customer_id", date_col="order_date", amount_col="amount",
                      reference_date=None, frame=None):
        """F는 서로 다른 구매일 수, M은 지정한 거래금액 컬럼의 합입니다.

        기본 amount는 load_data()에서 원본 price와 같은 값으로 생성합니다.
        다른 거래 데이터는 frame과 amount_col 인자로 지정할 수 있습니다.
        """
        data = self.df if frame is None else frame
        data = data[[customer_col, date_col, amount_col]].copy()
        data[date_col] = pd.to_datetime(data[date_col], errors="raise").dt.normalize()
        data[amount_col] = pd.to_numeric(data[amount_col], errors="raise")
        if data.empty or data.isna().any().any():
            raise ValueError("RFM에 사용할 완전한 거래 기록이 필요합니다.")
        if not np.isfinite(data[amount_col]).all() or (data[amount_col] < 0).any():
            raise ValueError("RFM 금액은 유한한 비음수여야 합니다.")
        ref = pd.Timestamp(reference_date).normalize() if reference_date is not None else data[date_col].max()
        if ref < data[date_col].max():
            raise ValueError("기준일은 최종 거래일보다 빠를 수 없습니다.")
        grouped = data.groupby(customer_col, sort=True)
        last = grouped[date_col].max()
        rfm = pd.DataFrame({"Recency": (ref - last).dt.days,
                            "Frequency": grouped[date_col].nunique(),
                            "Monetary": grouped[amount_col].sum()})
        # 동일 값에는 같은 점수. 순위를 억지로 나누거나 고객 ID로 동점을 깨지 않습니다.
        for metric, score, ascending in [("Recency", "R_score", False),
                                          ("Frequency", "F_score", True),
                                          ("Monetary", "M_score", True)]:
            percentile = rfm[metric].rank(method="average", pct=True, ascending=ascending)
            rfm[score] = np.ceil(percentile * 4).clip(1, 4).astype(int)
        r, f, m = rfm.R_score, rfm.F_score, rfm.M_score
        rfm["segment"] = np.select(
            [(r >= 3) & (f >= 3) & (m >= 3), (r >= 2) & (f >= 3),
             (r >= 3) & (f < 3), r == 1],
            ["VIP", "Loyal", "RecentLowFreq", "AtRisk"], default="Regular")
        self.rfm = rfm
        self.reference_date = ref
        return rfm

    def segment_summary(self):
        rfm = self.rfm
        result = rfm.groupby("segment").agg(customers=("Monetary", "size"),
            mean_recency_days=("Recency", "mean"), mean_purchase_days=("Frequency", "mean"),
            mean_monetary=("Monetary", "mean"), total_monetary=("Monetary", "sum"))
        result["customer_pct"] = result.customers / len(rfm) * 100
        total = rfm.Monetary.sum()
        result["monetary_pct"] = result.total_monetary / total * 100 if total > 0 else 0.0
        return result.reindex([s for s in self.SEGMENTS if s in result.index])

    def summary_statistics(self):
        """통계별 관찰 단위를 표시: 가격=거래, 나이=고객, 이미지/상품명=상품."""
        names = self.articles.prod_name.astype("string").str.len().astype(float)
        series = {"price / transaction": self.df.price, "age / customer": self.customers.age,
                  "name_length / product": names,
                  "image_mean / product": self.image_features.image_mean,
                  "image_std / product": self.image_features.image_std}
        return pd.DataFrame({name: values.describe() for name, values in series.items()})


class AnalysisOutputs:
    """단계별 결과를 같은 파일명으로 덮어쓰고 이번 실행의 저장 상태를 기록합니다.

    새 인스턴스는 현재 실행의 목록만 초기화합니다. 이전 실행의 파일은
    삭제하지 않으며, 이번 실행에서 저장한 파일만 목록에 포함합니다.
    """

    RESERVED_NAMES = {"readme.md", "run_status.json"}

    def __init__(self, output_dir):
        self.output_dir = Path(output_dir).expanduser().resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.files = {}
        self.status = "running"
        self._write_index()

    def _target(self, filename):
        name = str(filename)
        if (not name or name in {".", ".."} or Path(name).name != name
                or any(char in name for char in "/\\:\r\n")):
            raise ValueError("결과 파일명에는 폴더 경로를 넣지 마세요.")
        if name.casefold() in self.RESERVED_NAMES:
            raise ValueError("README.md와 run_status.json은 저장 상태 기록용 파일입니다.")
        target = self.output_dir / name
        if target.is_symlink():
            raise ValueError("심볼릭 링크를 결과 파일로 덮어쓸 수 없습니다.")
        return target

    def _temporary_path(self, target):
        with tempfile.NamedTemporaryFile(
                dir=self.output_dir, prefix="." + target.name + ".",
                suffix=".tmp", delete=False) as temporary:
            return Path(temporary.name)

    def _atomic_text(self, target, text):
        temporary = self._temporary_path(target)
        try:
            temporary.write_text(text, encoding="utf-8")
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)

    def _write_index(self):
        ordered = dict(sorted(self.files.items()))
        state = {"status": self.status, "files_written": list(ordered), "files": ordered}
        self._atomic_text(
            self.output_dir / "run_status.json",
            json.dumps(state, ensure_ascii=False, indent=2) + "\n")
        label = "완료" if self.status == "completed" else "진행 중 또는 미완료"
        lines = [
            "# 단계별 분석 결과", "",
            f"현재 실행 상태: **{label}** (`{self.status}`)", "",
            f"이번 실행에서 저장한 파일: **{len(ordered)}개**", "",
            "같은 단계는 항상 같은 파일명으로 저장하므로 다시 실행하면 해당 파일을 덮어씁니다.",
            "아래 목록에 없는 기존 파일은 이번 실행에서 갱신되지 않았습니다. 이전 실행의 파일이 남아 있을 수 있으며 자동으로 삭제하지 않습니다.",
            "분석이 중단되면 상태는 `running`으로 남습니다. 최종 결과를 확인할 때는 노트북을 처음부터 끝까지 실행하고 `completed`인지 확인하세요.", "",
            "CSV는 UTF-8 BOM 형식입니다. 고객·상품 ID의 앞자리 0을 유지하려면 CSV를 다시 읽거나 스프레드시트로 가져올 때 ID 컬럼을 문자열로 지정하세요.", "",
            "행·열 수는 저장된 CSV 기준이며, 이름 있는 인덱스를 저장한 경우 해당 인덱스도 열 수에 포함합니다.", "",
            "| 파일 | 종류 | 행 수 | 열 수 |",
            "|---|---|---:|---:|",
        ]
        kinds = {"csv": "표", "text": "설명·기록", "figure": "그래프"}
        for name, details in ordered.items():
            lines.append(
                f"| [{name}]({name}) | {kinds[details['kind']]} | "
                f"{details.get('rows', '—')} | {details.get('columns', '—')} |")
        if not ordered:
            lines.append("| 아직 저장된 단계 결과가 없습니다. | — | — | — |")
        self._atomic_text(self.output_dir / "README.md", "\n".join(lines) + "\n")

    def _save(self, filename, writer, details):
        target = self._target(filename)
        self.status = "running"
        self.files.pop(target.name, None)
        self._write_index()
        temporary = self._temporary_path(target)
        try:
            writer(temporary)
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
        # 저장에 성공한 파일만 이번 실행의 목록에 기록합니다.
        self.files[target.name] = details
        self._write_index()
        return target

    def save_table(self, filename, table, index=False, index_label=None):
        """전체 표를 CSV로 저장합니다. 고객 ID 등 의미 있는 인덱스는 명시하세요."""
        if isinstance(table, pd.Series):
            table = table.to_frame()
        if not isinstance(table, pd.DataFrame):
            raise TypeError("table에는 Pandas DataFrame 또는 Series를 전달하세요.")
        details = {"kind": "csv", "rows": len(table),
                   "columns": len(table.columns) + (table.index.nlevels if index else 0)}
        return self._save(
            filename,
            lambda path: table.to_csv(path, mode="w", encoding="utf-8-sig",
                                      index=index, index_label=index_label),
            details)

    def save_text(self, filename, text):
        """단계별 해석과 텍스트 출력을 저장합니다."""
        return self._save(
            filename, lambda path: path.write_text(str(text), encoding="utf-8"),
            {"kind": "text"})

    def save_figure(self, filename, fig):
        """Matplotlib Figure를 저장합니다. 확장자로 그림 형식을 지정합니다."""
        target = self._target(filename)
        image_format = target.suffix.lstrip(".").lower()
        if not image_format:
            raise ValueError("그래프 파일명에 .png와 같은 확장자를 넣으세요.")
        return self._save(
            filename,
            lambda path: fig.savefig(path, format=image_format, dpi=150, bbox_inches="tight"),
            {"kind": "figure"})

    def complete(self, required_files):
        """필요한 결과가 이번 실행에서 모두 저장됐을 때만 완료로 표시합니다."""
        targets = [self._target(name) for name in required_files]
        missing = [path.name for path in targets
                   if path.name not in self.files or not path.is_file()]
        if missing:
            self.status = "running"
            self._write_index()
            raise ValueError(f"이번 실행에서 저장되지 않은 필수 결과가 있습니다: {missing}")
        self.status = "completed"
        self._write_index()
        return self.output_dir
