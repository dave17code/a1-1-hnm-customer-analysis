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
    """노트북에서 생략한 거래·고객 명세를 고정된 CSV 세 개에 저장합니다."""

    REQUIRED_CSVS = (
        "01_loaded_transactions.csv",
        "03_cleaned_transactions.csv",
        "05_customer_rfm.csv",
    )
    _OLD_RESULTS = (
        "00_environment.txt", "01_data_info.txt", "01_load_notes.md",
        "01_age_summary_before.csv", "01_price_summary.csv",
        "02_age_imputation.csv", "02_customers_cleaned.csv", "02_featured_transactions.csv",
        "02_features_notes.md", "02_image_features.csv",
        "03_iqr_bounds.csv", "03_iqr_notes.md", "03_outlier_rows.csv", "03_preprocessing_log.csv",
        "04_statistics_notes.md", "04_summary_statistics.csv",
        "05_rfm_notes.md", "05_segment_summary.csv",
        "06_01_price_histogram.md", "06_01_price_histogram.png",
        "06_02_price_boxplot.md", "06_02_price_boxplot.png",
        "06_03_segment_counts.md", "06_03_segment_counts.png",
        "06_04_rfm_correlation.md", "06_04_rfm_correlation.png",
        "06_05_frequency_monetary.md", "06_05_frequency_monetary.png",
        "06_06_monthly_amount.md", "06_06_monthly_amount.png",
        "06_monthly_amount.csv", "06_rfm_correlations.csv", "07_analysis_report.md",
    )

    def __init__(self, output_dir):
        path = Path(output_dir).expanduser()
        if path.is_symlink():
            raise ValueError("결과 폴더는 심볼릭 링크가 아닌 폴더로 선택하세요.")
        self.output_dir = path.resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._written = set()

    def save_table(self, filename, table, index=False, index_label=None):
        """전체 표를 UTF-8 BOM CSV로 저장하고, 쓰기에 성공한 뒤 기존 파일을 교체합니다."""
        if filename not in self.REQUIRED_CSVS:
            raise ValueError(f"저장할 수 있는 전체 행 CSV: {self.REQUIRED_CSVS}")
        self._written.discard(filename)
        if not isinstance(table, (pd.Series, pd.DataFrame)):
            raise TypeError("table에는 Pandas DataFrame 또는 Series를 전달하세요.")
        target = self.output_dir / filename
        if target.is_symlink():
            raise ValueError(f"심볼릭 링크를 덮어쓸 수 없습니다: {filename}")
        with tempfile.NamedTemporaryFile(dir=self.output_dir, delete=False) as handle:
            temporary = Path(handle.name)
        try:
            table.to_csv(temporary, encoding="utf-8-sig", index=index, index_label=index_label)
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
        self._written.add(filename)
        return target

    def _remove_old_outputs(self):
        """이전 자동 생성 목록을 확인한 경우에만 알려진 기존 결과 파일을 정리합니다."""
        index = self.output_dir / "README.md"
        status = self.output_dir / "run_status.json"
        old_index = False
        if index.is_file() and not index.is_symlink():
            with index.open(encoding="utf-8-sig", errors="replace") as f:
                old_index = f.read(120).startswith("# 단계별 분석 결과\n\n현재 실행 상태: **")
        old_status = False
        if status.is_file() and not status.is_symlink():
            try:
                state = json.loads(status.read_text(encoding="utf-8-sig"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                state = None
            old_status = (
                isinstance(state, dict) and set(state) == {"status", "files_written", "files"}
                and state["status"] in ("running", "completed") and isinstance(state["files"], dict)
                and state["files_written"] == list(state["files"])
                and set(state["files"]).issubset(self.REQUIRED_CSVS + self._OLD_RESULTS)
                and (old_index or bool(state["files"]))
            )
        if old_index or old_status:
            for filename in self._OLD_RESULTS:
                path = self.output_dir / filename
                if path.is_file() and not path.is_symlink():
                    path.unlink(missing_ok=True)
        if old_index:
            index.unlink(missing_ok=True)
        if old_status:
            status.unlink(missing_ok=True)

    def complete(self):
        """이번 실행에서 CSV 세 개를 모두 썼는지 확인한 다음 이전 버전의 결과를 정리합니다."""
        for name in self.REQUIRED_CSVS:
            path = self.output_dir / name
            if name not in self._written or path.is_symlink() or not path.is_file():
                raise ValueError(f"이번 실행에서 전체 행 CSV를 저장했는지 확인하세요: {name}")
        self._remove_old_outputs()
        return self.output_dir
