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
        tallest = max(axes[0].patches, key=lambda bar: bar.get_height())
        left = tallest.get_x()
        right = left + tallest.get_width()
        bounds = a.outlier_report
        upper = bounds["upper"]
        above = df.amount.gt(upper).sum()
        upper_whisker = df.loc[df.amount.le(upper), "amount"].max()
        display(Markdown(f"""#### ① 왼쪽 히스토그램 · 어느 금액대의 거래가 가장 많을까요?

가로축은 H&M이 제공한 단위의 거래금액, 세로축은 거래 건수입니다. 막대 하나의 너비는 금액 구간이고 높이는 그 구간에 들어간 거래 수입니다.

가장 높은 막대부터 보세요. 약 `{left:.4f}~{right:.4f}` 구간에 {tallest.get_height():,.0f}건이 모여 있습니다. 반면 `0.15` 이상인 거래는 통틀어 {df.amount.ge(0.15).sum():,}건입니다. 세로축이 수천 건까지 올라가서 오른쪽의 작은 막대가 바닥선과 거의 겹쳐 보입니다. 거래금액의 중앙값은 `{df.amount.median():.4f}`이고, 소수의 고액 거래가 오른쪽으로 긴 꼬리를 만듭니다.

#### ② 오른쪽 박스플롯 · 금액이 큰 거래를 경계값으로 제한하면 무엇이 달라질까요?

아래쪽에 납작하게 색칠된 직사각형이 상자입니다. 왼쪽 `Original`은 원본 거래금액, 오른쪽 `IQR clipped`는 셀 04에서 만든 비교용 금액입니다.

| 그림에서 볼 부분 | 읽는 방법 |
|---|---|
| 상자의 아랫변과 윗변 | 아랫변은 Q1({bounds['q1']:.5f}), 윗변은 Q3({bounds['q3']:.5f})입니다. 거래금액의 가운데 절반이 이 사이에 있습니다. |
| 상자 안의 가로선 | 중앙값({df.amount.median():.5f})입니다. |
| 상자의 세로 높이 | `IQR = Q3 − Q1`로 구한 폭({bounds['iqr']:.5f})입니다. |
| 원본 상자에서 위로 뻗은 선(수염)의 끝 | 위쪽 경계를 넘지 않은 관측값 중 가장 큰 값({upper_whisker:.5f})입니다. |
| 원본 상자 위에 따로 찍힌 동그라미 | 위쪽 경계({upper:.5f})를 넘은 거래입니다. 금액이 같거나 비슷하면 점이 겹쳐 보입니다. |

셀 04에서 위쪽 경계를 넘은 {above:,}건의 비교용 금액을 경계까지 낮췄습니다. 가장 큰 거래 한 건을 따라가면 원본 `amount`는 {df.amount.max():.5f}, 비교용 `amount_iqr`는 {df.amount_iqr.max():.5f}입니다. 그래서 오른쪽에서는 위쪽 점들이 사라지고 두 상자의 가운데 부분은 거의 같은 높이에 남습니다. 양쪽 모두 {len(df):,}건입니다. 고객별·월별 구매금액은 원본을 더합니다."""))

        # 스피어만 계수는 각 지표의 순위 사이의 상관계수입니다. 동점은 평균 순위를 씁니다.
        rfm_ranks = rfm[["Recency", "Frequency", "Monetary"]].rank(method="average")
        self.correlation = rfm_ranks.corr()
        fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
        bars = axes[0].bar(segments.index, segments.customers, color=[palette[s] for s in segments.index])
        axes[0].bar_label(bars, padding=3)
        axes[0].margins(y=0.15)
        axes[0].tick_params(axis="x", labelrotation=12)
        axes[0].set(title="3. Customers by RFM segment", xlabel="Segment", ylabel="Customers")
        # 전체 상관행렬에서 대각선과 그 아래를 가린 뒤, 완전히 빈 마지막 행과 첫 열을 생략합니다.
        hide_lower = np.tril(np.ones(self.correlation.shape, dtype=bool))
        sns.heatmap(self.correlation.iloc[:-1, 1:], mask=hide_lower[:-1, 1:],
                    annot=True, fmt="+.2f", vmin=-1, vmax=1, center=0, cmap="vlag",
                    square=True, linewidths=1, linecolor="white", ax=axes[1],
                    cbar_kws={"label": "Spearman ρ"})
        axes[1].set(title="4. Spearman rank correlation", xlabel="RFM metric", ylabel="RFM metric")
        axes[1].grid(False)
        axes[1].tick_params(axis="y", labelrotation=0)
        self._show(fig, {3, 4})
        by_group = " · ".join(f"{name} {count:,}명" for name, count in segments.customers.items())
        largest = segments.customers.idxmax()
        rf = self.correlation.loc["Recency", "Frequency"]
        rm = self.correlation.loc["Recency", "Monetary"]
        fm = self.correlation.loc["Frequency", "Monetary"]
        first_id = df.customer_id.iloc[0]
        example = rfm.loc[first_id]
        example_ranks = rfm_ranks.loc[first_id]
        display(Markdown(f"""#### ③ 왼쪽 막대그래프 · 각 그룹에는 고객이 몇 명 있을까요?

막대 하나가 고객 그룹 하나입니다. 가로축에서 그룹을 고르고 막대 위의 숫자를 읽으면 그 그룹의 인원수를 알 수 있습니다.

{by_group}

{len(segments)}개 막대의 높이를 더하면 표본 고객 {len(rfm):,}명입니다. 가장 높은 {largest} 막대에는 전체 고객의 {segments.loc[largest, 'customer_pct']:.1f}%가 속합니다. VIP 유지 혜택이나 AtRisk 재방문 안내를 기획할 때 각 막대의 높이로 대상 규모를 가늠할 수 있습니다.

#### ④ RFM 지표 간 스피어만 순위상관

‘구매한 날짜가 많은 고객은 총구매금액도 큰 편일까?’를 알아보려고 고객 {len(rfm):,}명을 두 번 줄 세웠습니다. 한 번은 구매일 수가 적은 순서로, 한 번은 누적금액이 작은 순서로 세웁니다. 셀 02의 첫 고객은 {example.Frequency}일 구매해 첫 줄에서는 {example_ranks.Frequency:g}번째, 약 {example.Monetary:.2f}를 써서 둘째 줄에서는 {example_ranks.Monetary:g}번째입니다. 이 고객은 두 줄 모두 뒤쪽에 섭니다.

스피어만 계수는 모든 고객의 두 순서가 얼마나 비슷한지를 −1에서 +1 사이로 요약합니다. 두 순서가 비슷할수록 +1, 반대로 정렬될수록 −1에 가까워집니다. 서로 같은 값을 가진 고객은 그들이 차지하는 자리의 평균 순위를 받습니다. 이 계산에는 셀 06의 1~4점으로 묶기 전인 실제 미구매 일수(R), 구매일 수(F), 누적금액(M)을 사용합니다.

| 그림 속 위치 | 비교한 두 순위 | 스피어만 계수 | 이 표본에서의 의미 |
|---|---|---:|---|
| 왼쪽 위 | 미구매 일수(R)와 구매일 수(F) | {rf:+.2f} | 마지막 구매 후 오래 지난 고객은 R이 큰 쪽에, 구매일 수는 적은 쪽에 서는 경향이 있었습니다. 두 순서가 반대 방향이어서 음수입니다. |
| 오른쪽 위 | 미구매 일수(R)와 누적금액(M) | {rm:+.2f} | 마지막 구매가 오래전인 고객일수록 누적금액이 작은 쪽에 서는 경향이 있었습니다. |
| 오른쪽 아래 | 구매일 수(F)와 누적금액(M) | {fm:+.2f} | 여러 날 구매한 고객일수록 누적금액도 큰 쪽에 섰습니다. 같은 고객이 두 줄에서 비슷한 위치에 서는 경향이어서 양수입니다. |

왼쪽 아래는 구매일 수(F)를 자기 자신과 비교하는 자리여서 비워 두었습니다.

##### 실제 구매금액으로 읽는 F–M 관계

아래 표에서 같은 구매일 수 구간에 속한 고객 중 가운데에 해당하는 누적 구매금액(중앙값)을 비교해 보세요. 금액은 H&M 제공 단위입니다. 히트맵 계수는 {len(rfm):,}명의 개별 순위로 구했고, 이 표는 그 경향을 실제 금액으로 살펴보기 위한 요약입니다."""))
        purchase_days = pd.cut(rfm.Frequency, bins=[0, 1, 2, 3, np.inf],
                               labels=["1일", "2일", "3일", "4일 이상"])
        spend_by_days = rfm.groupby(purchase_days, observed=True)["Monetary"].agg(
            고객_수="size", 누적금액_중앙값="median")
        spend_by_days.index.name = "구매일 수"
        display(spend_by_days.round(4))

        start, end = pd.Timestamp(a.meta["window_start"]), pd.Timestamp(a.meta["reference_date"])
        months = pd.period_range(start, end, freq="M")
        self.monthly = df.groupby(df.order_date.dt.to_period("M")).amount.sum().reindex(months, fill_value=0)
        month_table = self.monthly.rename("amount").to_frame()
        month_table.index.name = "month"
        month_table["observed_days"] = [
            (min(p.end_time.normalize(), end) - max(p.start_time, start)).days + 1 for p in months]
        month_table["is_partial"] = [p.start_time < start or p.end_time.normalize() > end for p in months]
        display(Markdown("##### ⑥ 라인차트에 사용하는 월별 구매금액"))
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
        purchases = df.customer_id.eq(first_id).sum()
        fewest_days = rfm.Frequency.min()
        same_days = rfm.loc[rfm.Frequency.eq(fewest_days), "Monetary"]
        peak = self.monthly.idxmax()
        partial_months = month_table.loc[month_table.is_partial, "observed_days"]
        partial_text = ", ".join(f"{month.month}월 {days}일치" for month, days in partial_months.items())
        display(Markdown(f"""#### ⑤ 왼쪽 산점도 · 구매한 날짜 수가 같으면 지출도 비슷할까요?

점 하나가 고객 한 명입니다. 오른쪽으로 갈수록 구매한 날짜가 많고 위로 갈수록 누적 구매금액이 큽니다. 색은 셀 06에서 배정한 그룹을 나타냅니다.

셀 02의 첫 고객을 이 그림에 찍으면 가로 {example.Frequency}일, 세로 약 {example.Monetary:.2f}입니다. 이 고객의 거래는 {purchases:,}행이지만 같은 날 여러 상품을 산 기록을 하루로 세기 때문에 가로 위치는 {example.Frequency}입니다.

가로축 `{fewest_days}`에서 점들이 세로로 늘어선 부분을 보세요. 이 위치에 있는 {len(same_days):,}명은 똑같이 {fewest_days}일 구매했지만, 구매금액은 {same_days.min():.4f}에서 {same_days.max():.4f}까지 퍼져 있습니다. ④의 F–M 칸은 두 순위의 관계를 요약합니다. 이 산점도는 실제 일수와 금액으로 그리기 때문에, 같은 일수만큼 구매한 사람들 사이의 지출 차이까지 보입니다.

#### ⑥ 오른쪽 라인차트 · 어느 달에 표본 고객의 총구매금액이 가장 컸을까요?

가로축은 달, 세로축은 그달 표본 고객들의 원본 거래금액을 모두 더한 값입니다. 가장 높은 점은 {peak.year}년 {peak.month}월의 {self.monthly.loc[peak]:.4f}입니다. 바로 위 월별 표의 `amount` 열에서 다른 달의 정확한 합계도 확인할 수 있습니다.

가로축의 `partial`은 관찰 기간이 그달의 일부만 포함한다는 표시입니다. 관찰 기간은 {start.date()}부터 {end.date()}까지입니다. {partial_text + '의 거래가 포함됩니다.' if partial_text else '이 기간에는 달 전체를 관찰했습니다.'} 첫 달이나 마지막 달의 합계가 작아 보이면, 표의 `observed_days`에서 며칠을 관찰했는지 먼저 확인하세요."""))

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
        assert np.isfinite(self.correlation.to_numpy()).all()
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
