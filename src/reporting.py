"""노트북의 표·그래프·해석을 간결하게 표시합니다.

계산 규칙은 DataAnalyzer에 두고, 이 모듈은 결과 표시와 제출물 갱신을 담당합니다.
"""
from pathlib import Path
import tempfile

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from IPython.display import display, Markdown


class AnalysisReport:
    def __init__(self, analyzer, root, outputs):
        self.analyzer = analyzer
        self.root = Path(root)
        self.outputs = outputs
        self.shown_charts = set()
        self.correlation = None
        self.monthly = None
        sns.set_theme(style="whitegrid", context="notebook")
        plt.rcParams.update({"figure.dpi": 110, "font.size": 10})

    @staticmethod
    def _notes(observation, implication):
        display(Markdown(f"**관찰:** {observation}\n\n**의미:** {implication}"))

    def overview(self):
        a = self.analyzer
        preview = a.df.head().copy()
        preview["customer_id"] = preview.customer_id.str[:8] + "…"
        display(preview)
        a.df.info()
        display(a.df[["amount"]].describe().round(4))
        self._notes(
            f"입력은 **{len(a.df):,}행 × {a.df.shape[1]}컬럼**, 고객 **{len(a.customers):,}명**, "
            f"상품 **{len(a.articles):,}개**, 상품 종류 **{a.df.product_type_name.nunique():,}개**이며 기간은 **{a.meta['window_start']}~{a.meta['reference_date']}**입니다.",
            "고객·상품이 이미 결합된 표입니다. 고객 나이는 고객별 한 번, 상품 특성은 상품별 한 번 집계하여 "
            "구매가 많은 대상이 통계에 반복 반영되지 않게 합니다. 상품 종류는 범주형 자료로 확인하며 금액은 제공 단위입니다.")

    def features(self):
        a = self.analyzer
        changes = a.age_imputation.copy()
        changes["customer_id"] = changes.customer_id.str[:8] + "…"
        display(changes)
        display(a.df[["article_id", "prod_name", "name_length", "image_mean", "image_std", "image_missing"]].head(3))
        missing = len(a.articles) - len(a.image_ids)
        coverage = len(a.image_ids) / len(a.articles) * 100
        self._notes(
            f"나이 결측 **{len(changes):,}명**을 대치하고 이미지 **{len(a.image_ids):,}개**에서 평균·표준편차를 "
            f"계산했습니다. 이미지 연결률은 **{coverage:.2f}%**, 사진 없는 상품은 **{missing}개**입니다.",
            "대치한 나이는 추정값입니다. 사진 없는 상품의 거래는 유지하고 이미지 특성만 NaN으로 남깁니다. "
            "이미지 숫자에는 배경·조명도 포함되므로 상품 품질이나 고객 선호를 뜻하지 않습니다.")

    def outliers(self):
        a, out = self.analyzer, self.analyzer.outlier_report
        display(pd.DataFrame([out]).round(6))
        self._notes(
            f"Q1={out['q1']:.4f}, Q3={out['q3']:.4f}, IQR={out['iqr']:.4f}이고 경계는 "
            f"**[{out['lower']:.4f}, {out['upper']:.4f}]**입니다. **{out['count']:,}행({out['rate']:.2%})**을 탐지했습니다.",
            "높은 거래금액이 오류라는 뜻은 아닙니다. 비교용 amount_iqr만 경계값으로 제한하고 원본 amount와 "
            "모든 거래 행은 보존합니다. 처리 전후 분포는 6단계의 박스플롯에서 비교합니다.")
        print(f"전체 가공 거래표 저장: outputs/03_cleaned_transactions.csv "
              f"({len(a.df):,}행 × {len(self.outputs.TRANSACTION_COLUMNS)}컬럼)")

    def statistics(self, stats):
        display(stats.round(4))
        amount = stats["amount / transaction"]
        self._notes(
            f"거래금액 평균 **{amount['mean']:.4f}**, 중앙값 **{amount['50%']:.4f}**, 표준편차 **{amount['std']:.4f}**, "
            f"Q1~Q3는 **{amount['25%']:.4f}~{amount['75%']:.4f}**입니다. "
            f"고객 나이 중앙값은 **{self.analyzer.customers.age.median():.1f}세**입니다.",
            "중심과 퍼짐을 함께 보면 평균만으로 놓치는 거래금액 차이를 읽을 수 있습니다. 나이 통계에는 대치값이 포함됩니다. "
            "표의 이미지 통계는 상품별로 계산한 이미지 평균·표준편차를 다시 요약한 것입니다.")

    def rfm_summary(self, segments):
        a = self.analyzer
        display(segments[["customers", "customer_pct", "mean_recency_days", "mean_purchase_days", "mean_monetary", "monetary_pct"]].round(2))
        self._notes(
            f"**{a.reference_date.date()}**를 기준으로 고객 **{len(a.rfm):,}명**을 **{a.rfm.segment.nunique()}개 그룹**으로 "
            f"분류했습니다. 구매일 수 중앙값은 **{a.rfm.Frequency.median():.1f}일**, 미구매 기간 중앙값은 "
            f"**{a.rfm.Recency.median():.1f}일**입니다.",
            "Frequency는 서로 다른 구매 날짜 수이며 주문·방문 횟수가 아닙니다. RecentLowFreq는 최근 저빈도 고객, "
            "AtRisk는 상대적으로 오래 구매하지 않은 고객으로 신규 가입·이탈 확정을 뜻하지 않습니다.")
        print(f"고객별 RFM 전체 표 저장: outputs/05_customer_rfm.csv ({len(a.rfm):,}행)")

    def _show(self, figure, chart_ids):
        figure.tight_layout()
        plt.show()
        plt.close(figure)
        self.shown_charts.update(chart_ids)

    def charts(self):
        a, df = self.analyzer, self.analyzer.df
        rfm, segments = a.rfm, a.segment_summary()
        palette = dict(zip(a.SEGMENTS, sns.color_palette("colorblind", len(a.SEGMENTS))))
        self.shown_charts.clear()

        fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
        sns.histplot(data=df, x="amount", bins=30, ax=axes[0], color="#4477AA")
        axes[0].set(title="1. Transaction amount distribution", xlabel="Amount (provided units)", ylabel="Transaction rows")
        sns.boxplot(data=df[["amount", "amount_iqr"]].rename(columns={"amount": "Original", "amount_iqr": "IQR clipped"}), ax=axes[1])
        axes[1].set(title="2. Amount before and after IQR treatment", xlabel="Treatment", ylabel="Amount (provided units)")
        self._show(fig, {1, 2})
        self._notes(
            f"**① 히스토그램:** 거래금액 중앙값 **{df.amount.median():.4f}**, 범위 **{df.amount.min():.4f}~{df.amount.max():.4f}**. "
            f"**② 박스플롯:** 표준편차 **{df.amount.std():.4f} → {df.amount_iqr.std():.4f}**, "
            f"최댓값 **{df.amount.max():.4f} → {df.amount_iqr.max():.4f}**.",
            "① 중심 구간과 고액 거래의 긴 꼬리를 함께 확인해야 대표 거래금액을 설명할 수 있습니다. "
            "② 극단값 제한으로 분포가 얼마나 달라지는지 비교합니다. RFM에는 제한하지 않은 amount를 사용합니다.")

        self.correlation = rfm[["Recency", "Frequency", "Monetary"]].corr(method="pearson")
        fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
        bars = axes[0].bar(segments.index, segments.customers, color=[palette[s] for s in segments.index])
        axes[0].bar_label(bars, padding=3)
        axes[0].margins(y=0.15)
        axes[0].tick_params(axis="x", labelrotation=12)
        axes[0].set(title="3. Customers by RFM segment", xlabel="Segment", ylabel="Customers")
        sns.heatmap(self.correlation, annot=True, fmt=".2f", vmin=-1, vmax=1, center=0,
                    cmap="vlag", square=True, ax=axes[1], cbar_kws={"label": "Pearson r"})
        axes[1].set(title="4. RFM correlation", xlabel="RFM metric", ylabel="RFM metric")
        self._show(fig, {3, 4})
        largest = segments.customers.idxmax()
        rf, fm = self.correlation.loc["Recency", "Frequency"], self.correlation.loc["Frequency", "Monetary"]
        self._notes(
            f"**③ 막대그래프:** 가장 큰 그룹은 **{largest}, {int(segments.loc[largest, 'customers']):,}명"
            f"({segments.loc[largest, 'customer_pct']:.1f}%)**입니다. **④ 히트맵:** R–F 상관계수 **{rf:.3f}**, F–M **{fm:.3f}**입니다.",
            "③ 고객 수와 금액 기여도를 함께 보고 캠페인 규모를 정할 수 있습니다. "
            "④ R–F가 음수이면 최근 구매 고객에서 구매일 수가 많은 경향이고, F–M이 양수이면 구매일 수와 금액이 함께 커지는 경향입니다. "
            "누적 구매 구조의 영향도 있으므로 상관관계가 인과관계를 증명하지는 않습니다.")

        start, end = pd.Timestamp(a.meta["window_start"]), pd.Timestamp(a.meta["reference_date"])
        months = pd.period_range(start, end, freq="M")
        self.monthly = df.groupby(df.order_date.dt.to_period("M")).amount.sum().reindex(months, fill_value=0)
        month_table = self.monthly.rename("amount").to_frame()
        month_table.index.name = "month"
        month_table["observed_days"] = [
            (min(p.end_time.normalize(), end) - max(p.start_time, start)).days + 1 for p in months]
        month_table["is_partial"] = [p.start_time < start or p.end_time.normalize() > end for p in months]
        display(month_table.round(4))
        labels = [str(p) + ("\n(partial)" if partial else "") for p, partial in zip(months, month_table.is_partial)]
        fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
        sns.scatterplot(data=rfm, x="Frequency", y="Monetary", hue="segment", palette=palette, alpha=.65, s=30, ax=axes[0])
        axes[0].set(title="5. Purchase days and total spend", xlabel="Distinct purchase days", ylabel="Total spend (provided units)")
        axes[0].legend(title="Segment", fontsize=8)
        axes[1].plot(labels, self.monthly.to_numpy(), marker="o", color="#4477AA")
        axes[1].tick_params(axis="x", labelsize=8)
        axes[1].set(title="6. Monthly spend of sampled customers", xlabel="Month in observation window", ylabel="Total spend (provided units)")
        self._show(fig, {5, 6})
        peak = self.monthly.idxmax()
        self._notes(
            f"**⑤ 산점도:** 고객 **{len(rfm):,}명**, 구매일 수 **{rfm.Frequency.min()}~{rfm.Frequency.max()}일**, "
            f"금액 **{rfm.Monetary.min():.4f}~{rfm.Monetary.max():.4f}**입니다. "
            f"**⑥ 라인차트:** **{len(months)}개 달력월** 중 최고 합계는 **{peak}, {self.monthly.loc[peak]:.4f}**입니다.",
            "⑤ 같은 구매일 수에서도 금액 차이를 볼 수 있습니다. 색은 RFM으로 정한 그룹이므로 독립적인 예측 성능은 아닙니다. "
            "⑥ partial은 한 달 일부만 관측한 구간입니다. 첫 달·마지막 달의 낮은 합계를 곧바로 매출 하락으로 해석할 수 없습니다.")

    def _validate(self):
        a, df, rfm = self.analyzer, self.analyzer.df, self.analyzer.rfm
        assert a.base_shape[0] >= 1000 and a.base_shape[1] >= 8
        assert {"customer_id", "order_date", "amount"}.issubset(df.columns)
        assert pd.api.types.is_datetime64_any_dtype(df.order_date)
        assert pd.api.types.is_numeric_dtype(df.amount)
        assert isinstance(df.product_type_name.dtype, pd.CategoricalDtype)
        assert len(df) == a.base_shape[0] == a.meta["transactions"]
        assert len(a.customers) == df.customer_id.nunique() == len(rfm) == a.meta["customers"]
        assert len(a.articles) == df.article_id.nunique() == a.meta["products"]
        assert not a.customers.customer_id.duplicated().any()
        assert not a.articles.article_id.duplicated().any()
        assert np.array_equal(a.raw_amount.to_numpy(), df.amount.to_numpy())
        assert np.isclose(rfm.Monetary.sum(), df.amount.sum())
        assert self.monthly is not None and np.isclose(self.monthly.sum(), df.amount.sum())
        assert a.customers.age.notna().all() and len(a.age_imputation) > 0
        assert len(a.image_ids) == len(a.image_features) > 0
        assert rfm.segment.nunique() >= 4
        assert rfm[["R_score", "F_score", "M_score"]].isin([1, 2, 3, 4]).all().all()
        assert np.isfinite([self.correlation.loc["Recency", "Frequency"], self.correlation.loc["Frequency", "Monetary"]]).all()
        assert self.shown_charts == {1, 2, 3, 4, 5, 6}
        self.outputs.complete()

    def finish(self):
        self._validate()
        a, segments = self.analyzer, self.analyzer.segment_summary()
        actions = {
            "VIP": ("VIP 고객 유지", "VIP에게 우선 구매·멤버십 혜택을 제공하여 재구매 유지율 향상을 기대합니다.",
                    "혜택 비용·마진·후속 구매 데이터가 필요합니다. 대조군보다 순이익이 개선되지 않으면 제안을 재검토합니다."),
            "AtRisk": ("장기 미구매 고객 재활성화", "AtRisk에게 구매 이력 기반 재방문 캠페인을 시험하여 재구매 전환을 기대합니다.",
                       "수신 동의·노출·후속 구매 데이터가 필요합니다. 대조군과 차이가 없으면 미구매 기간에 근거한 타기팅을 재검토합니다."),
            "RecentLowFreq": ("최근 저빈도 고객의 반복 구매", "RecentLowFreq에게 최근 구매 상품과 관련된 안내를 제공하여 다음 구매를 유도합니다.",
                             "가입일·관찰 기간 이전 구매·캠페인 반응 데이터가 필요합니다. 현재 표본만으로 실제 신규 고객인지는 알 수 없습니다."),
            "Loyal": ("반복 구매 고객 유지", "Loyal에게 자주 구매한 범주의 혜택을 시험하여 구매 간격 유지와 구매금액 증가를 기대합니다.",
                      "카테고리별 마진·후속 구매 데이터가 필요합니다. 할인으로 순이익이 감소하면 혜택 방식을 바꿉니다."),
            "Regular": ("일반 고객의 추가 탐색", "Regular를 구매 범주별로 나누어 관련 상품을 안내하고 반복 구매를 기대합니다.",
                        "관심·노출·클릭·후속 구매 데이터가 필요합니다. 구매 전환 차이가 없으면 세분화 기준을 재검토합니다."),
        }
        insights = []
        targets = [s for s in ["VIP", "AtRisk", "RecentLowFreq", "Loyal", "Regular"] if s in segments.index][:3]
        for i, segment in enumerate(targets, 1):
            row = segments.loc[segment]
            title, action, verification = actions[segment]
            insights.append(
                f"**인사이트 {i}. {title}**\n\n"
                f"- **근거:** {segment} **{int(row.customers):,}명({row.customer_pct:.1f}%)**, 평균 미구매 기간 "
                f"**{row.mean_recency_days:.1f}일**, 평균 구매일 수 **{row.mean_purchase_days:.2f}일**, "
                f"평균 금액 **{row.mean_monetary:.4f}**, 전체 표본 금액 비중 **{row.monetary_pct:.1f}%**입니다.\n"
                f"- **실행:** {action}\n- **검증:** {verification}\n")
        results = (
            f"관찰 기간 **{a.meta['window_start']}~{a.meta['reference_date']}**, 거래 **{len(a.df):,}행**, "
            f"고객 **{len(a.rfm):,}명**, **{a.rfm.segment.nunique()}개 세그먼트**입니다. "
            f"나이 결측 **{len(a.age_imputation)}명**을 대치했고, 거래금액 이상치는 **{a.outlier_report['count']:,}행**입니다.\n\n"
            + "\n".join(insights)
            + "\n금액은 제공 단위이며 기대 효과는 검증할 가설입니다. 근거는 "
              "[분석 노트북](notebooks/analysis_report.ipynb)의 5단계 요약표와 6단계 차트입니다.\n")
        readme = self.root / "README.md"
        existing = readme.read_text(encoding="utf-8")
        begin, end = "<!-- ANALYSIS_RESULTS_START -->", "<!-- ANALYSIS_RESULTS_END -->"
        if existing.count(begin) != 1 or existing.count(end) != 1:
            raise ValueError("README에 분석 결과 시작·종료 표시가 각각 하나씩 있어야 합니다.")
        prefix, rest = existing.split(begin, 1)
        _, suffix = rest.split(end, 1)
        content = prefix + begin + "\n\n" + results + "\n" + end + suffix
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=self.root, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
        try:
            temporary.replace(readme)
        finally:
            temporary.unlink(missing_ok=True)
        display(Markdown(results))
        print("검증 완료: 거래·원본 금액 보존, 고객·상품 분석 단위, RFM 합계, 결측치 대치, 6종 차트, 상세 CSV 2개, 거래 CSV 11컬럼")
        print("README 분석 결과 갱신 완료. 노트북을 Windows Ctrl+S / Mac Cmd+S로 저장하세요.")
