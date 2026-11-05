# 단계별 분석 결과

현재 실행 상태: **완료** (`completed`)

이번 실행에서 저장한 파일: **36개**

같은 단계는 항상 같은 파일명으로 저장하므로 다시 실행하면 해당 파일을 덮어씁니다.
아래 목록에 없는 기존 파일은 이번 실행에서 갱신되지 않았습니다. 이전 실행의 파일이 남아 있을 수 있으며 자동으로 삭제하지 않습니다.
분석이 중단되면 상태는 `running`으로 남습니다. 최종 결과를 확인할 때는 노트북을 처음부터 끝까지 실행하고 `completed`인지 확인하세요.

CSV는 UTF-8 BOM 형식입니다. 고객·상품 ID의 앞자리 0을 유지하려면 CSV를 다시 읽거나 스프레드시트로 가져올 때 ID 컬럼을 문자열로 지정하세요.

행·열 수는 저장된 CSV 기준이며, 이름 있는 인덱스를 저장한 경우 해당 인덱스도 열 수에 포함합니다.

| 파일 | 종류 | 행 수 | 열 수 |
|---|---|---:|---:|
| [00_environment.txt](00_environment.txt) | 설명·기록 | — | — |
| [01_age_summary_before.csv](01_age_summary_before.csv) | 표 | 8 | 2 |
| [01_data_info.txt](01_data_info.txt) | 설명·기록 | — | — |
| [01_load_notes.md](01_load_notes.md) | 설명·기록 | — | — |
| [01_loaded_transactions.csv](01_loaded_transactions.csv) | 표 | 11153 | 12 |
| [01_price_summary.csv](01_price_summary.csv) | 표 | 8 | 2 |
| [02_age_imputation.csv](02_age_imputation.csv) | 표 | 3 | 4 |
| [02_customers_cleaned.csv](02_customers_cleaned.csv) | 표 | 1000 | 3 |
| [02_featured_transactions.csv](02_featured_transactions.csv) | 표 | 11153 | 16 |
| [02_features_notes.md](02_features_notes.md) | 설명·기록 | — | — |
| [02_image_features.csv](02_image_features.csv) | 표 | 6047 | 3 |
| [03_cleaned_transactions.csv](03_cleaned_transactions.csv) | 표 | 11153 | 18 |
| [03_iqr_bounds.csv](03_iqr_bounds.csv) | 표 | 1 | 9 |
| [03_iqr_notes.md](03_iqr_notes.md) | 설명·기록 | — | — |
| [03_outlier_rows.csv](03_outlier_rows.csv) | 표 | 535 | 19 |
| [03_preprocessing_log.csv](03_preprocessing_log.csv) | 표 | 4 | 5 |
| [04_statistics_notes.md](04_statistics_notes.md) | 설명·기록 | — | — |
| [04_summary_statistics.csv](04_summary_statistics.csv) | 표 | 8 | 6 |
| [05_customer_rfm.csv](05_customer_rfm.csv) | 표 | 1000 | 8 |
| [05_rfm_notes.md](05_rfm_notes.md) | 설명·기록 | — | — |
| [05_segment_summary.csv](05_segment_summary.csv) | 표 | 5 | 8 |
| [06_01_price_histogram.md](06_01_price_histogram.md) | 설명·기록 | — | — |
| [06_01_price_histogram.png](06_01_price_histogram.png) | 그래프 | — | — |
| [06_02_price_boxplot.md](06_02_price_boxplot.md) | 설명·기록 | — | — |
| [06_02_price_boxplot.png](06_02_price_boxplot.png) | 그래프 | — | — |
| [06_03_segment_counts.md](06_03_segment_counts.md) | 설명·기록 | — | — |
| [06_03_segment_counts.png](06_03_segment_counts.png) | 그래프 | — | — |
| [06_04_rfm_correlation.md](06_04_rfm_correlation.md) | 설명·기록 | — | — |
| [06_04_rfm_correlation.png](06_04_rfm_correlation.png) | 그래프 | — | — |
| [06_05_frequency_monetary.md](06_05_frequency_monetary.md) | 설명·기록 | — | — |
| [06_05_frequency_monetary.png](06_05_frequency_monetary.png) | 그래프 | — | — |
| [06_06_monthly_amount.md](06_06_monthly_amount.md) | 설명·기록 | — | — |
| [06_06_monthly_amount.png](06_06_monthly_amount.png) | 그래프 | — | — |
| [06_monthly_amount.csv](06_monthly_amount.csv) | 표 | 7 | 4 |
| [06_rfm_correlations.csv](06_rfm_correlations.csv) | 표 | 3 | 4 |
| [07_analysis_report.md](07_analysis_report.md) | 설명·기록 | — | — |
