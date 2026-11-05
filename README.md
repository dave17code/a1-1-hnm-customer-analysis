# A1-1 · H&M 고객 구매 패턴 분석

H&M의 거래·고객·상품·이미지 샘플을 활용하여 구매 패턴을 분석하고, RFM으로 고객을 세분화하는 프로젝트입니다.

NumPy와 Pandas로 데이터를 전처리하고 통계를 계산하며, Matplotlib과 Seaborn으로 결과를 시각화합니다. 분석 로직은 `DataAnalyzer` 클래스로 구성했습니다.

노트북에서 표·그래프·해석을 확인할 수 있으며, 각 단계의 결과는 프로젝트 최상위 `outputs` 폴더에도 저장됩니다. 다시 실행하면 같은 이름의 결과 파일을 덮어씁니다.

보너스 과제는 포함하지 않습니다.

## 1. 데이터 구성

프로젝트 최상위에 다음 입력 파일 5개가 있습니다.

| 파일 | 역할 | 규모 |
|---|---|---|
| `transactions.csv` | 고객별 구매 기록 | 11,153행 |
| `customers.csv` | 고객의 나이·회원 상태 | 1,000명 |
| `articles.csv` | 상품명·종류·색상 | 6,055개 상품 |
| `images.npz` | 상품 이미지의 NumPy 배열 | 6,047개, 각각 64×64×3 |
| `provenance.json` | 데이터 출처·샘플 추출 조건·누락 정보 | 기간·시드·선택 방법 등 |

### 샘플 추출 범위

- 관찰 기간: **2020-03-23~2020-09-22**
- 난수 시드: **42**
- 해당 기간에 구매한 고객 중 **1,000명**을 선택했습니다.
- 선택된 고객의 관찰 기간 내 거래를 함께 확보했습니다.
- 거래에 연결되는 고객·상품 정보와 해당 상품의 이미지를 포함했습니다.
- 이미지가 없는 상품 **8개**는 이미지 누락 상태로 남겼습니다.

이 샘플은 서로 연결된 데이터입니다. 거래의 `customer_id`로 고객 정보를, `article_id`로 상품 정보와 이미지 특성을 연결합니다.

데이터 파일은 프로젝트 최상위에 유지합니다. 별도의 `data/sample` 폴더로 옮기거나 다시 추출할 필요가 없습니다.

### 분석 단위

| 분석 대상 | 기준 |
|---|---|
| 가격 분포 | 거래 기록 한 행 |
| 고객 나이 | 고객 한 명 |
| 상품명·이미지 특성 | 상품 한 개 |
| RFM | 고객 한 명의 관찰 기간 내 구매 기록 |
| 월별 금액 | 해당 월의 거래금액 합계 |

한 거래 행을 정확한 주문 한 건이나 방문 한 회로 해석하지 않습니다.

### 거래 입력 컬럼 대응

| 분석 컬럼 | 생성 방법 | 의미 |
|---|---|---|
| `customer_id` | 원본 값을 문자열로 유지 | 고객 식별자 |
| `order_date` | 원본 `t_dat`의 이름을 변경하고 날짜형으로 변환 | 구매 날짜 |
| `amount` | 원본 거래행 `price`를 그대로 복사 | 분석용 거래금액, 제공 단위 유지 |

`amount`는 `load_data()`에서 생성합니다. 원본 CSV는 수정하지 않습니다.

수량이나 주문 총액을 추정하지 않으며, 금액을 원화나 달러로 임의 환산하지 않습니다. RFM의 Monetary와 월별 금액 합계는 `amount`를 사용합니다.

고객·상품 정보는 거래 표를 기준으로 LEFT JOIN하며, `many_to_one` 검증으로 연결 관계를 확인합니다. 연결 과정에서 거래 11,153행을 보존합니다.

## 2. 코드와 결과 파일

| 경로 | 역할 |
|---|---|
| `requirements.txt` | 분석 도구와 설치 버전 |
| `src/pipeline.py` | 데이터 분석과 결과 저장 클래스 |
| `notebooks/analysis_report.ipynb` | 분석 실행·표·그래프·해석 |
| `README.md` | 프로젝트 설명·실행 방법·비즈니스 인사이트 |
| `outputs/` | 단계별 CSV·그래프·해석·실행 상태 |

### DataAnalyzer

`src/pipeline.py`의 분석 클래스입니다.

| 메서드 | 역할 |
|---|---|
| `load_data()` | 입력 파일 읽기, 날짜·금액 정리, 고객·상품 정보 연결 |
| `handle_missing_values()` | 고객 그룹별 통계를 활용한 결측값 대치 |
| `engineer_features()` | 이미지 평균·표준편차와 상품명 길이 생성 |
| `detect_outliers()` | IQR 이상치 탐지와 비교용 처리 컬럼 생성 |
| `summary_statistics()` | 분석 단위별 기술통계 계산 |
| `calculate_rfm()` | 고객별 RFM 값·점수·세그먼트 계산 |
| `segment_summary()` | 고객 세그먼트별 요약 통계 |

이미지 평균과 표준편차는 이미지 배열의 축을 지정한 NumPy 벡터 연산으로 계산합니다.

상품명 길이는 Pandas 문자열 연산으로 계산합니다.

### AnalysisOutputs

같은 파일에 정의된 결과 저장 클래스입니다.

| 메서드 | 역할 |
|---|---|
| `save_table()` | 전체 표를 CSV로 저장 |
| `save_figure()` | 그래프를 PNG로 저장 |
| `save_text()` | 해석·정보를 텍스트 파일로 저장 |
| `complete()` | 필요한 결과 파일이 저장됐는지 확인하고 완료 상태 기록 |

저장 기능을 추가해도 노트북 안의 표·그래프·해석 출력은 그대로 유지됩니다.

## 3. 가상환경과 분석 도구 설치

이 프로젝트는 **Python 3.12**를 기준으로 구성했습니다.

각 컴퓨터에서 별도의 `.venv`를 만듭니다. Windows의 가상환경을 Mac으로 복사하거나, 다른 컴퓨터의 `.venv`를 그대로 사용하지 않습니다.

이미 프로젝트의 가상환경과 분석 도구를 설치했다면 이 단계는 건너뛰어도 됩니다.

아래 명령은 프로젝트 최상위 폴더에서 실행합니다. 가상환경의 Python을 경로로 직접 실행하므로 활성화 여부와 관계없이 해당 환경에 도구가 설치됩니다.

### Windows PowerShell

```powershell
py -3.12 --version
py -3.12 -m venv .venv

.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -c "import sys, numpy, pandas, matplotlib, seaborn, ipykernel; print(sys.executable); print('분석 환경 준비 완료')"
```

`py` 명령이 없고 `python --version`이 `3.12.x`라면 가상환경 생성 명령을 다음과 같이 바꿀 수 있습니다.

```powershell
python -m venv .venv
```

가상환경 생성 이후의 명령은 그대로 사용합니다.

### Mac

```bash
python3.12 --version
python3.12 -m venv .venv

./.venv/bin/python3 -m pip install --upgrade pip
./.venv/bin/python3 -m pip install -r requirements.txt

./.venv/bin/python3 -m pip check
./.venv/bin/python3 -c "import sys, numpy, pandas, matplotlib, seaborn, ipykernel; print(sys.executable); print('분석 환경 준비 완료')"
```

`python3.12` 명령이 없지만 `python3 --version`이 `3.12.x`라면 가상환경 생성 명령을 다음과 같이 바꿀 수 있습니다.

```bash
python3 -m venv .venv
```

### 설치 확인

- Python 버전이 `3.12.x`인지 확인합니다.
- `pip check` 결과가 `No broken requirements found.`인지 확인합니다.
- 마지막 명령에서 현재 프로젝트의 `.venv` 경로와 `분석 환경 준비 완료`가 출력되는지 확인합니다.

### 사용 도구

설치 버전은 `requirements.txt`에 기록되어 있습니다.

| 도구 | 설치 버전 | 역할 |
|---|---|---|
| NumPy | 2.3.5 | 이미지 배열의 평균·표준편차 계산 |
| Pandas | 2.2.3 | CSV 읽기, 연결, 결측값 처리, 통계, RFM |
| Matplotlib | 3.10.8 | 그래프 생성과 파일 저장 |
| Seaborn | 0.13.2 | 분포·상관관계·고객 비교 시각화 |
| IPyKernel | 6.29 이상, 8 미만 | VS Code 노트북 실행 |

분석에는 NumPy·Pandas·Matplotlib·Seaborn을 사용합니다. IPyKernel은 노트북 실행 환경 도구입니다.

분석 코드에서 OpenCV, Pillow, Scikit-learn, NLTK, 자동 EDA 라이브러리를 직접 사용하지 않습니다.

## 4. VS Code에서 Python과 노트북 커널 선택

### Python 인터프리터 선택

1. VS Code에서 프로젝트 폴더를 엽니다.
2. 확장에서 Microsoft의 **Python**과 **Jupyter**를 설치합니다.
3. 명령 팔레트를 엽니다.
   - Windows: `Ctrl+Shift+P`
   - Mac: `Cmd+Shift+P`
4. `Python: Select Interpreter`를 실행합니다.
5. 현재 프로젝트의 `.venv` 환경을 선택합니다.

실행 파일 경로는 다음과 같습니다.

| 운영체제 | 프로젝트 안의 실행 파일 |
|---|---|
| Windows | `.venv\Scripts\python.exe` |
| Mac | `.venv/bin/python` |

다른 프로젝트의 `.venv`가 아닌 현재 프로젝트의 환경을 선택합니다.

### 노트북 커널 선택

1. `notebooks/analysis_report.ipynb`를 엽니다.
2. 노트북 오른쪽 위의 커널 이름 또는 **Select Kernel**을 누릅니다.
3. 필요하면 **Select Another Kernel → Python Environments**로 이동합니다.
4. 현재 프로젝트의 `.venv`를 선택합니다.

Python 인터프리터 선택과 노트북 커널 선택은 각각 확인합니다.

목록에 가상환경이 나타나지 않으면 명령 팔레트에서 `Developer: Reload Window`를 실행한 뒤 다시 선택합니다.

### 실제 실행 환경 확인

노트북에서 `from pathlib import Path`로 시작하는 첫 번째 코드 셀 왼쪽의 실행 버튼을 누릅니다.

출력의 `실행 중인 Python` 경로가 현재 프로젝트의 `.venv`를 가리키는지 확인합니다.

Mac 실행 예시는 다음과 같습니다.

```text
실행 중인 Python: /Users/사용자명/Desktop/a1-1-hnm-customer-analysis/.venv/bin/python
프로젝트 및 데이터 위치: /Users/사용자명/Desktop/a1-1-hnm-customer-analysis
단계별 결과 저장 위치: /Users/사용자명/Desktop/a1-1-hnm-customer-analysis/outputs
```

사용자명과 프로젝트 위치는 컴퓨터마다 달라집니다.

## 5. 노트북 실행 순서

노트북에는 설명을 담은 Markdown 셀과 실행 가능한 코드 셀이 있습니다.

처음 공부할 때는 위에서 아래로 코드 셀을 하나씩 실행하며 결과를 확인합니다. 셀 왼쪽의 실행 버튼이나 `Shift+Enter`를 사용할 수 있습니다.

중간 셀부터 실행하면 이전 셀에서 만든 변수가 없어 오류가 날 수 있습니다.

| 순서 | 분석 내용 | 확인할 내용 |
|---|---|---|
| 1 | 환경과 경로 확인 | 프로젝트 `.venv`와 입력 파일 위치 |
| 2 | 데이터 로드·연결·기본 탐색 | 11,153행 유지, 12컬럼, 자료형과 기본 통계 |
| 3 | 결측값 처리·피처 생성 | 나이 대치, 이미지 평균·표준편차, 상품명 길이 |
| 4 | IQR 이상치 탐지 | 경계값, 탐지 건수, 원본 가격과 비교용 가격 |
| 5 | 기술통계 | 평균·중앙값·표준편차·사분위수 |
| 6 | RFM 고객 세분화 | 고객별 R·F·M, 점수, 그룹 |
| 7 | 시각화 | 그래프 6개와 수치 해석 |
| 8 | 계산 검증·인사이트 | 합계·행 수·그룹 수 확인, 최종 인사이트 |

최종 실행 결과를 저장할 때는 다음 순서로 진행합니다.

1. 노트북의 커널이 현재 프로젝트 `.venv`인지 확인합니다.
2. **Restart Kernel**로 커널을 재시작합니다.
3. **Run All**로 모든 코드 셀을 실행합니다.
4. 마지막 셀의 검증·저장 완료 메시지를 확인합니다.
5. Windows는 `Ctrl+S`, Mac은 `Cmd+S`로 노트북을 저장합니다.

완료 메시지에는 다음 내용이 포함됩니다.

```text
필수 계산 검증 통과
README 결과 영역 갱신 완료
단계별 결과 저장 완료: .../outputs (CSV 16개 · PNG 6개)
```

코드 셀은 총 **13개**입니다.

노트북 마지막 셀은 이 README의 자동 갱신 영역에 실제 분석 결과를 기록합니다. 해당 영역의 시작·종료 주석은 삭제하지 않습니다.

## 6. 단계별 결과 파일

각 분석 단계가 실행되면 `outputs` 폴더에 결과를 저장합니다.

모든 셀이 CSV를 하나씩 만드는 방식은 아닙니다. 표를 계산하는 셀에서 해당 단계의 CSV를 저장하고, 그래프를 만드는 셀에서 PNG와 해석을 저장합니다.

### 저장되는 파일 수

| 종류 | 개수 | 내용 |
|---|---:|---|
| CSV | 16개 | 단계별 전체 표와 통계 |
| PNG | 6개 | 그래프 |
| 분석 Markdown | 12개 | 단계·차트 해석과 최종 리포트 |
| TXT | 2개 | 실행 환경과 `info()` 출력 |
| 관리 파일 | 2개 | `outputs/README.md`, `run_status.json` |
| 합계 | **38개** | |

`outputs/README.md`를 먼저 열면 이번 실행의 상태와 저장된 파일 목록을 확인할 수 있습니다.

### CSV 파일

아래 행·컬럼 수는 현재 샘플 기준입니다.

| 단계 | 파일 | 내용 |
|---|---|---|
| 데이터 로드 | `01_loaded_transactions.csv` | 고객·상품 정보를 연결한 전체 거래 표, 11,153행 × 12컬럼 |
| 데이터 로드 | `01_price_summary.csv` | 거래 가격의 기본 통계 |
| 데이터 로드 | `01_age_summary_before.csv` | 대치 전 고객 나이 통계 |
| 결측·피처 | `02_age_imputation.csv` | 나이 결측 고객 3명의 대치 전·후 값 |
| 결측·피처 | `02_customers_cleaned.csv` | 결측 처리 후 고객 1,000명 |
| 결측·피처 | `02_image_features.csv` | 이미지 6,047개의 평균·표준편차 |
| 결측·피처 | `02_featured_transactions.csv` | 이미지·상품명 피처를 추가한 거래 표, 11,153행 × 16컬럼 |
| IQR | `03_outlier_rows.csv` | 이상치로 탐지된 거래 535행 |
| IQR | `03_cleaned_transactions.csv` | 이상치 표시·비교용 가격을 추가한 거래 표, 11,153행 × 18컬럼 |
| IQR | `03_preprocessing_log.csv` | 결측·이미지 누락·가격 처리 내역 |
| IQR | `03_iqr_bounds.csv` | Q1·Q3·IQR·경계·탐지 건수 |
| 기술통계 | `04_summary_statistics.csv` | 거래·고객·상품 단위의 기술통계 |
| RFM | `05_customer_rfm.csv` | 고객 1,000명의 RFM 값·점수·그룹 |
| RFM | `05_segment_summary.csv` | 5개 그룹의 고객 수·평균 RFM·금액 비중 |
| 상관관계 | `06_rfm_correlations.csv` | RFM 상관행렬 |
| 월별 집계 | `06_monthly_amount.csv` | 월별 금액·관찰 일수·일부 기간 여부 |

CSV에는 화면에 표시한 `head()` 미리보기만 저장하는 것이 아니라 해당 표의 **전체 행**을 저장합니다.

`03_outlier_rows.csv`의 `transaction_row`는 연결된 거래 표의 0부터 시작하는 행 번호입니다. 실제 주문 ID를 뜻하지 않습니다.

CSV는 UTF-8 BOM 형식으로 저장합니다. `customer_id`와 `article_id`는 문자열 식별자이며, 상품 ID 앞자리 `0`을 유지해야 합니다.

CSV를 Pandas로 다시 읽는 예시는 다음과 같습니다.

```python
import pandas as pd

loaded = pd.read_csv(
    "outputs/01_loaded_transactions.csv",
    dtype={
        "customer_id": str,
        "article_id": str,
        "sales_channel_id": str,
    },
    parse_dates=["order_date"],
)

loaded.head()
```

위 경로 예시는 프로젝트 최상위에서 실행하는 경우입니다.

### 그래프 파일

| 파일 | 그래프 |
|---|---|
| `06_01_price_histogram.png` | 가격 분포 히스토그램 |
| `06_02_price_boxplot.png` | 이상치 처리 전후 박스플롯 |
| `06_03_segment_counts.png` | 세그먼트별 고객 수 막대그래프 |
| `06_04_rfm_correlation.png` | RFM 상관계수 히트맵 |
| `06_05_frequency_monetary.png` | 구매일 수와 구매금액 산점도 |
| `06_06_monthly_amount.png` | 월별 구매금액 라인차트 |

각 PNG와 같은 이름의 `.md` 파일에는 그래프의 수치 근거와 시사점이 저장됩니다.

### 설명과 실행 기록

| 파일 | 내용 |
|---|---|
| `00_environment.txt` | Python 버전·실행 파일·프로젝트 경로·NumPy/Pandas 버전 |
| `01_data_info.txt` | 연결한 거래 표의 `info()` 출력 |
| `01_load_notes.md` | 데이터 로드 단계의 해석 |
| `02_features_notes.md` | 결측값·이미지·텍스트 피처 해석 |
| `03_iqr_notes.md` | 이상치 탐지 결과 해석 |
| `04_statistics_notes.md` | 기술통계 해석 |
| `05_rfm_notes.md` | RFM 분석 해석 |
| `07_analysis_report.md` | 최종 요약·세그먼트 표·비즈니스 인사이트 |
| `README.md` | 이번 실행 상태와 저장된 파일 목록 |
| `run_status.json` | 실행 상태·파일 목록·CSV 행 및 컬럼 수 |

이 표의 파일들은 모두 `outputs` 폴더 안에 있습니다.

## 7. 반복 실행과 결과 덮어쓰기

분석을 다시 수행하려면 다음 순서로 실행합니다.

**커널 재시작 → 모든 셀 실행 → 완료 메시지 확인 → 노트북 저장**

동일한 단계는 항상 같은 이름으로 저장합니다.

- 기존 CSV는 새로 계산한 전체 표로 덮어씁니다.
- 기존 PNG는 새 그래프로 덮어씁니다.
- 단계별 해석과 최종 리포트도 갱신합니다.
- 노트북 안의 표·그래프·해석도 다시 표시됩니다.
- 프로젝트 README의 자동 분석 결과 영역도 갱신합니다.

CSV 뒤에 행을 이어 붙이거나 날짜별 사본을 계속 만들지 않습니다. 재실행 전에 결과 파일을 직접 삭제할 필요는 없습니다.

### 실행 상태 확인

첫 번째 코드 셀을 실행하면 이번 실행의 파일 목록을 초기화하고 상태를 `running`으로 기록합니다.

마지막 셀은 필요한 결과 파일이 모두 저장됐는지 확인한 후 상태를 `completed`로 변경합니다.

중간에 오류나 중단이 발생하면 아직 실행하지 않은 단계의 이전 파일이 남아 있을 수 있습니다. 이 경우 `outputs/README.md`의 상태와 이번 실행 파일 목록을 확인합니다.

최종 결과로 사용할 때는 전체 실행이 끝나고 상태가 `completed`인지 확인합니다.

### 원본 데이터 보존

분석과 결과 저장 과정에서 다음 입력 파일은 변경하지 않습니다.

- `transactions.csv`
- `customers.csv`
- `articles.csv`
- `images.npz`
- `provenance.json`

## 8. 분석 결과를 해석하는 기준

### 고객·상품·거래의 구분

같은 고객이나 상품은 여러 거래 행에 반복해서 나타날 수 있습니다.

따라서 고객 나이는 고객별 한 행에서, 상품명 길이와 이미지 특성은 상품별 한 행에서 통계를 계산합니다.

### RFM 정의

| 지표 | 계산 기준 | 의미 |
|---|---|---|
| Recency | 기준일 − 마지막 구매일 | 마지막 구매 후 경과 일수 |
| Frequency | 서로 다른 구매 날짜 수 | 관찰 기간 내 구매한 날짜 수 |
| Monetary | 거래행 `amount` 합계 | 제공 단위의 누적 구매금액 |

기준일은 **2020-09-22**입니다.

Frequency는 정확한 주문 횟수나 방문 횟수가 아닙니다. Monetary는 원본 `price`와 같은 값인 `amount`의 합계이며, 통화 환산을 하지 않습니다.

### 결측값과 이미지

나이 결측값은 회원 상태 그룹별 중앙값으로 대치합니다. 그룹 통계가 없으면 전체 고객의 중앙값을 사용합니다.

대치한 값은 추정값이며, 관측된 나이와 구별하여 해석합니다.

이미지가 없는 상품 8개의 거래는 유지합니다. 해당 상품이 포함된 거래 41행에는 이미지 특성이 결측으로 남습니다.

이미지 평균·표준편차는 축소한 64×64 RGB 배열 전체의 픽셀 통계입니다. 배경·조명·포장도 반영되므로 상품 품질이나 구매 선호를 직접 나타내는 값으로 단정하지 않습니다.

### 이상치 처리

IQR은 다음과 같이 계산합니다.

```text
IQR = Q3 - Q1
하한 = Q1 - 1.5 × IQR
상한 = Q3 + 1.5 × IQR
```

범위 밖의 가격을 이상치로 표시합니다.

원본 `price`와 `amount`는 보존하고, 비교용 `price_iqr` 컬럼에 경계값으로 제한한 가격을 저장합니다. 거래를 삭제하지 않습니다.

RFM과 월별 금액 집계에는 원본 가격과 같은 `amount`를 사용합니다.

### 월별 비교와 일반화 범위

관찰 기간은 약 6개월이지만 달력상으로는 3월부터 9월까지 7개 월에 걸칩니다.

3월과 9월은 일부 날짜만 포함되어 있으므로 전체 월과 같은 조건으로 비교하지 않습니다. 월별 CSV에 관찰 일수와 일부 기간 여부를 함께 기록합니다.

분석 결과의 범위는 표본 고객 1,000명과 선택한 관찰 기간입니다. 전체 H&M 고객의 특성이나 실제 신규·이탈 여부로 바로 일반화하지 않습니다.

상관계수는 변수의 동반 변화를 나타내며, 인과관계를 증명하지 않습니다.

## 9. 실행 및 결과 검증

최신 저장 결과는 Mac의 프로젝트 `.venv`에서 실행했습니다.

| 항목 | 확인 내용 |
|---|---|
| Python | 3.12.16 |
| NumPy | 2.3.5 |
| Pandas | 2.2.3 |
| 코드 셀 | 13개가 순서대로 실행됨 |
| 저장된 실행 오류 | 없음 |
| 노트북 그래프 | 6개 |
| CSV 파일 | 16개 |
| PNG 파일 | 6개 |
| `outputs` 전체 파일 | 38개 |
| 최종 실행 상태 | `completed` |
| 원본 입력 파일 | 5개 모두 보존 |

다음 내용도 확인했습니다.

- 단계별 CSV에 전체 행이 저장됩니다.
- 고객 ID 전체와 상품 ID 앞자리 `0`이 보존됩니다.
- 연결 후 거래 11,153행이 유지됩니다.
- 원본 `price`와 분석용 `amount`가 일치합니다.
- 고객별 RFM 합계와 월별 금액 합계가 일치합니다.
- 고객은 5개 세그먼트로 분류됩니다.
- 노트북·README·별도 리포트의 분석 결과가 일치합니다.
- 고정 파일명으로 덮어쓰는 저장 기능이 적용되어 있습니다.
- 기존 노트북의 표·그래프·해석 출력이 유지됩니다.

실행 환경은 `outputs/00_environment.txt`에서 확인할 수 있습니다.

## 10. 분석 결과

아래 영역은 노트북 마지막 셀에서 자동으로 갱신합니다.

<!-- ANALYSIS_RESULTS_START -->
## 실제 분석 결과

실행 입력: 프로젝트 최상위의 샘플 파일 5개. 관찰 기간 **2020-03-23~2020-09-22**, 시드 **42**, 거래 **11,153행**, 고객 **1,000명**, 상품 **6,055개**.

나이 결측치 **3명** 대치, 상품 이미지 연결률 **99.87%**, 가격 IQR 탐지 **535행(4.80%)**. 원본 가격은 보존하고, 같은 값의 `amount`를 RFM과 월별 금액 집계에 사용했다.

거래 입력은 `customer_id`, `order_date`, `amount`를 포함한다. `order_date`는 원본 `t_dat`의 이름을 바꾸고, `amount`는 원본 거래행의 `price`를 그대로 복사해 생성했다. 수량과 주문 총액을 추정하지 않으며, 금액은 제공 단위를 유지한다.

| 그룹 | 고객 수 | 고객 비중 | 평균 R(일) | 평균 F(구매일) | 평균 M(제공 단위) | 금액 비중 |
|---|---:|---:|---:|---:|---:|---:|
| VIP | 302 | 30.2% | 21.0 | 6.06 | 0.6164 | 62.0% |
| Loyal | 223 | 22.3% | 59.1 | 2.87 | 0.2388 | 17.7% |
| RecentLowFreq | 123 | 12.3% | 25.6 | 1.00 | 0.1046 | 4.3% |
| AtRisk | 250 | 25.0% | 136.4 | 1.45 | 0.1566 | 13.0% |
| Regular | 102 | 10.2% | 79.6 | 1.00 | 0.0861 | 2.9% |

### 인사이트 1. VIP 유지

- **근거:** VIP는 302명(30.2%)이며, 평균 미구매 기간 21.0일, 평균 구매일 수 6.06일, 평균 총구매금액 0.6164(제공 단위), 전체 표본 구매금액 비중 62.0%다.
- **실행:** VIP 고객에게 우선 구매·멤버십 혜택을 제공해 재구매 유지율 향상을 기대한다.
- **검증:** 혜택 비용·마진·후속 구매 데이터가 필요하며, 무작위 대조군보다 순이익이 개선되지 않으면 제안을 재검토한다.

### 인사이트 2. 장기 미구매 고객 재활성화

- **근거:** AtRisk는 250명(25.0%)이며, 평균 미구매 기간 136.4일, 평균 구매일 수 1.45일, 평균 총구매금액 0.1566(제공 단위), 전체 표본 구매금액 비중 13.0%다.
- **실행:** AtRisk 고객에게 구매 이력 기반 재방문 캠페인을 시험해 재구매 전환을 기대한다.
- **검증:** 수신 동의·캠페인 노출·후속 구매 데이터가 필요하며, 대조군과 차이가 없으면 미구매 기간만으로 타기팅한 가설을 재검토한다.

### 인사이트 3. 최근 저빈도 고객의 반복 구매

- **근거:** RecentLowFreq는 123명(12.3%)이며, 평균 미구매 기간 25.6일, 평균 구매일 수 1.00일, 평균 총구매금액 0.1046(제공 단위), 전체 표본 구매금액 비중 4.3%다.
- **실행:** RecentLowFreq 고객에게 최근 구매 상품과 관련된 안내를 제공해 다음 구매를 유도한다.
- **검증:** 가입일·관찰 기간 이전 구매·캠페인 반응 데이터가 필요하다. 실제 신규 고객 여부는 현재 표본만으로 확인할 수 없다.

근거: [실행된 분석 노트북](notebooks/analysis_report.ipynb)의 RFM 요약표와 차트 3~5. 기대 효과는 실험할 가설이며 이미 달성한 성과가 아니다. 표본 밖 고객이나 관찰 기간 이전 이력으로 일반화하지 않는다.
<!-- ANALYSIS_RESULTS_END -->

## 11. 데이터 출처와 참고 문서

- 원본 데이터: [H&M Personalized Fashion Recommendations — Kaggle](https://www.kaggle.com/competitions/h-and-m-personalized-fashion-recommendations/data)
- 샘플 추출 조건: [provenance.json](provenance.json)
- 실행된 분석 노트북: [analysis_report.ipynb](notebooks/analysis_report.ipynb)
- 단계별 결과 목록: [outputs/README.md](outputs/README.md)
- Python 가상환경: [Python venv 문서](https://docs.python.org/3.12/library/venv.html)
- VS Code 노트북: [Jupyter Notebooks in VS Code](https://code.visualstudio.com/docs/datascience/jupyter-notebooks)
- VS Code 커널 선택: [Jupyter Kernel Management](https://code.visualstudio.com/docs/datascience/jupyter-kernel-management)

데이터 이용 조건은 `provenance.json`에 `Subject to Competition Rules`로 기록되어 있으며, 원본 대회의 이용 규정을 따릅니다.