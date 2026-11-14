"""A1-1: 고객 단위 표본을 분석하는 재사용 가능한 파이프라인.

분석에는 NumPy와 Pandas를 사용합니다. 노트북은 각 메서드를 순서대로 호출합니다.
"""
from pathlib import Path
import json
import tempfile

import numpy as np
import pandas as pd


class DataAnalyzer:
    SEGMENTS = ["VIP", "Loyal", "RecentLowFreq", "AtRisk", "Regular"]

    def __init__(self, data_path=None):
        # 분석 입력은 미리 결합한 CSV, 이미지 배열, 출처 기록 세 파일입니다.
        self.data_path = (Path(data_path).expanduser().resolve() if data_path is not None
                          else Path(__file__).resolve().parents[1])
        self.df = None
        self.customers = None
        self.articles = None
        self.image_features = None
        self.rfm = None
        self.reference_date = None
        self.outlier_report = None
        self.age_imputation = None
        self.base_shape = None
        self.raw_amount = None

    def load_data(self):
        """사전 결합한 샘플을 읽고, 고객·상품별 분석 단위를 구분합니다."""
        p = self.data_path
        required = ["analysis_input.csv", "images.npz", "provenance.json"]
        missing = [name for name in required if not (p / name).is_file()]
        if missing:
            raise FileNotFoundError(f"데이터 폴더 {p}에 필요한 파일이 없습니다: {missing}")
        self.meta = json.loads((p / "provenance.json").read_text(encoding="utf-8-sig"))
        frame = pd.read_csv(p / "analysis_input.csv", dtype=str,
                            keep_default_na=False).replace("", np.nan)
        required_columns = ["order_date", "customer_id", "article_id", "amount",
                            "prod_name", "product_type_name", "club_member_status", "age"]
        missing_columns = sorted(set(required_columns) - set(frame.columns))
        if missing_columns:
            raise ValueError(f"분석 입력에 필요한 컬럼이 없습니다: {missing_columns}")
        frame = frame[required_columns].copy()
        if frame.empty:
            raise ValueError("분석 입력이 비어 있습니다.")
        frame["order_date"] = pd.to_datetime(frame["order_date"], format="%Y-%m-%d", errors="raise")
        for column in ["amount", "age"]:
            frame[column] = pd.to_numeric(frame[column], errors="raise")
        if frame[["customer_id", "article_id", "order_date", "amount"]].isna().any().any():
            raise ValueError("거래의 필수 값이 누락되었습니다. 분석 입력을 확인하세요.")
        if not frame.customer_id.str.fullmatch(r"[0-9a-f]{64}").all():
            raise ValueError("H&M 고객 ID는 64자리 소문자 16진수 문자열이어야 합니다.")
        if not frame.article_id.str.fullmatch(r"[0-9]{10}").all():
            raise ValueError("H&M 상품 ID는 앞의 0을 보존한 10자리 문자열이어야 합니다.")
        if not np.isfinite(frame.amount).all() or (frame.amount < 0).any():
            raise ValueError("음수 또는 비유한 거래금액이 있습니다.")
        if not np.isfinite(frame.age.dropna().to_numpy()).all():
            raise ValueError("관측된 고객 나이는 유한한 숫자여야 합니다.")

        # 같은 ID가 거래마다 다른 속성을 가지면 임의로 한 값을 선택하지 않습니다.
        customer_columns = ["customer_id", "club_member_status", "age"]
        article_columns = ["article_id", "prod_name", "product_type_name"]
        customers = frame[customer_columns].drop_duplicates()
        articles = frame[article_columns].drop_duplicates()
        if customers.customer_id.duplicated().any():
            raise ValueError("같은 고객 ID에 서로 다른 고객 정보가 있습니다. 결측 여부도 확인하세요.")
        if articles.article_id.duplicated().any():
            raise ValueError("같은 상품 ID에 서로 다른 상품 정보가 있습니다. 결측 여부도 확인하세요.")
        self.customers = customers.reset_index(drop=True)
        self.articles = articles.reset_index(drop=True)
        self.df = frame
        self.df["product_type_name"] = self.df.product_type_name.astype("category")
        with np.load(p / "images.npz", allow_pickle=False) as images:
            self.image_ids = images["article_ids"].astype(str)
            self.pixels = images["pixels"]
        if self.pixels.ndim != 4 or self.pixels.shape[-1] != 3 or self.pixels.dtype != np.uint8:
            raise ValueError("이미지는 (N, H, W, 3)의 uint8 RGB 배열이어야 합니다.")
        if self.image_ids.ndim != 1 or len(self.image_ids) != len(self.pixels) or len(np.unique(self.image_ids)) != len(self.image_ids):
            raise ValueError("이미지 ID와 배열의 대응이 잘못되었습니다.")
        if not pd.Series(self.image_ids).isin(self.articles.article_id).all():
            raise ValueError("상품 표본에 속하지 않는 이미지가 있습니다.")
        self.base_shape = self.df.shape
        self.raw_amount = self.df.amount.copy()
        self.rfm = None
        self.reference_date = None
        self.outlier_report = None
        self.image_features = None
        self.age_imputation = None
        return self.df

    def handle_missing_values(self, strategy="group_median", group_col="club_member_status", column="age"):
        """고객별 한 행에서 그룹 통계를 계산해 구매 빈도에 의한 가중을 방지합니다."""
        if strategy not in {"group_median", "group_mean"}:
            raise ValueError("strategy는 group_median 또는 group_mean입니다.")
        customers = self.customers.copy()
        customers[column] = pd.to_numeric(customers[column], errors="raise")
        missing_rows = customers[column].isna()
        self.age_imputation = customers.loc[missing_rows, ["customer_id", group_col, column]].copy()
        self.age_imputation = self.age_imputation.rename(columns={column: "age_before"})
        customers[group_col] = customers[group_col].fillna("Unknown")
        values = customers[column]
        agg = "median" if strategy == "group_median" else "mean"
        group_values = customers.groupby(group_col, dropna=False)[column].transform(agg)
        fallback = getattr(values, agg)()
        if pd.isna(fallback):
            raise ValueError("표본에 관측된 나이가 없어 대치할 수 없습니다.")
        customers[column] = values.fillna(group_values).fillna(fallback)
        self.age_imputation["age_after"] = self.age_imputation.customer_id.map(
            customers.set_index("customer_id")[column])
        self.customers = customers
        lookup = customers.set_index("customer_id")
        self.df[column] = self.df.customer_id.map(lookup[column])
        self.df[group_col] = self.df.customer_id.map(lookup[group_col]).astype("category")
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
        return self.df

    def detect_outliers(self, column="amount", threshold=1.5, treatment="clip"):
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

        amount에는 H&M 원본 거래행의 금액을 그대로 보존합니다.
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
        """통계별 관찰 단위를 표시: 금액=거래, 나이=고객, 이미지/상품명=상품."""
        names = self.articles.prod_name.astype("string").str.len().astype(float)
        series = {"amount / transaction": self.df.amount, "age / customer": self.customers.age,
                  "name_length / product": names,
                  "image_mean / product": self.image_features.image_mean,
                  "image_std / product": self.image_features.image_std}
        return pd.DataFrame({name: values.describe() for name, values in series.items()})


class AnalysisOutputs:
    """거래 11컬럼과 고객별 RFM의 전체 행을 고정된 CSV 두 개에 저장합니다."""

    TRANSACTION_COLUMNS = [
        "order_date", "customer_id", "article_id", "amount",
        "prod_name", "product_type_name", "club_member_status", "age",
        "image_mean", "image_std", "name_length",
    ]

    REQUIRED_CSVS = (
        "03_cleaned_transactions.csv",
        "05_customer_rfm.csv",
    )
    def __init__(self, output_dir):
        path = Path(output_dir).expanduser()
        if path.is_symlink():
            raise ValueError("결과 폴더는 심볼릭 링크가 아닌 폴더로 선택하세요.")
        self.output_dir = path.resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._written = set()

    def save_table(self, filename, table, index=False, index_label=None):
        """거래표는 지정한 11컬럼만 저장합니다. 분석 중인 원래 표는 바꾸지 않습니다."""
        if filename not in self.REQUIRED_CSVS:
            raise ValueError(f"저장할 수 있는 전체 행 CSV: {self.REQUIRED_CSVS}")
        self._written.discard(filename)
        if not isinstance(table, (pd.Series, pd.DataFrame)):
            raise TypeError("table에는 Pandas DataFrame 또는 Series를 전달하세요.")
        if filename == "03_cleaned_transactions.csv":
            if not isinstance(table, pd.DataFrame) or index:
                raise ValueError("거래표는 DataFrame으로 전달하고 index=False로 저장하세요.")
            table = table.loc[:, self.TRANSACTION_COLUMNS]
        target = self.output_dir / filename
        if target.is_symlink():
            raise ValueError(f"심볼릭 링크를 덮어쓸 수 없습니다: {filename}")
        with tempfile.NamedTemporaryFile(dir=self.output_dir, delete=False) as handle:
            temporary = Path(handle.name)
        try:
            table.to_csv(temporary, encoding="utf-8-sig", index=index,
                         index_label=index_label, lineterminator="\n")
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
        self._written.add(filename)
        return target

    def complete(self):
        """이번 실행에서 필요한 CSV 두 개를 모두 저장했는지 확인합니다."""
        for name in self.REQUIRED_CSVS:
            path = self.output_dir / name
            if name not in self._written or path.is_symlink() or not path.is_file():
                raise ValueError(f"이번 실행에서 전체 행 CSV를 저장했는지 확인하세요: {name}")
        columns = pd.read_csv(self.output_dir / "03_cleaned_transactions.csv", nrows=0).columns.tolist()
        if columns != self.TRANSACTION_COLUMNS:
            raise ValueError("거래 결과 CSV의 컬럼은 지정한 11개와 순서가 일치해야 합니다.")
        return self.output_dir
