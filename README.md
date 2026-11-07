# A1-1 · H&M 고객 구매 패턴 분석

H&M의 거래·고객·상품·이미지 샘플을 활용하여 구매 패턴을 분석하고, RFM으로 고객을 세분화하는 프로젝트입니다.

NumPy와 Pandas로 데이터를 전처리하고 통계를 계산하며, Matplotlib과 Seaborn으로 결과를 시각화합니다. 분석 로직은 `DataAnalyzer` 클래스로 구성했습니다.

요약표, 그래프 6개와 해석은 [분석 노트북](notebooks/analysis_report.ipynb)에서 읽습니다. 거래별 상세 내역과 고객별 RFM은 [outputs/](outputs/)의 CSV에서 확인할 수 있습니다.

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
| `outputs/` | 노트북에서 전체 행을 펼쳐 보기 어려운 상세 CSV |

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

### 상세 표 저장

`AnalysisOutputs.save_table()`은 전체 행을 담은 표를 고정된 파일명으로 저장합니다. 마지막 셀이 호출하는 `complete()`는 이번 실행에서 대상 CSV 세 개가 모두 저장됐는지 확인합니다. 저장 시점과 파일 이름은 아래 6절에 정리했습니다.

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
| Matplotlib | 3.10.8 | 노트북에 표시할 그래프 생성 |
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

노트북 맨 위에서 환경을 설정하는 첫 번째 코드 셀을 찾고, 코드 왼쪽의 실행 버튼을 누릅니다.

출력의 `실행 중인 Python` 경로가 현재 프로젝트의 `.venv`를 가리키는지 확인합니다.

Mac 실행 예시는 다음과 같습니다.

```text
실행 중인 Python: /Users/사용자명/Desktop/a1-1-hnm-customer-analysis/.venv/bin/python
프로젝트 및 데이터 위치: /Users/사용자명/Desktop/a1-1-hnm-customer-analysis
전체 행 CSV 저장 위치: /Users/사용자명/Desktop/a1-1-hnm-customer-analysis/outputs
```

사용자명과 프로젝트 위치는 컴퓨터마다 달라집니다.

## 5. 노트북 실행 순서

노트북에는 설명을 담은 Markdown 셀과 실행 가능한 코드 셀이 있습니다.

처음 공부할 때는 위에서 아래로 코드 셀을 하나씩 실행하며 결과를 확인합니다. 셀 왼쪽의 실행 버튼이나 `Shift+Enter`를 사용할 수 있습니다.

중간 셀부터 실행하면 이전 셀에서 만든 변수가 없어 오류가 날 수 있습니다.

코드 위에 표시한 셀 번호는 노트북에서의 고정 순서입니다. VS Code의 대괄호 속 숫자는 커널에서 실행한 순서이므로, 같은 셀을 다시 실행하면 달라질 수 있습니다.

| 큰 제목 | 코드 셀 | 실행 내용 |
|---|---|---|
| 실행 준비 | 01 | 파이썬 환경과 프로젝트 경로 확인 |
| 1. 데이터 로드와 분석 단위 | 02 | 고객·상품 정보를 연결한 거래 표의 행 수, 자료형, 기본 통계 확인 |
| 2. 그룹별 결측치 대치와 멀티모달 피처 | 03 | 나이 대치, 이미지 평균·표준편차와 상품명 길이 계산 |
| 3. IQR 탐지와 처리 기록 | 04 | 이상치 탐지, 원본 가격과 비교용 가격 구분 |
| 4. 기술통계 | 05 | 평균·중앙값·표준편차·사분위수 확인 |
| 5. RFM 점수와 고객 세분화 | 06 | 고객별 R·F·M과 세그먼트 계산 |
| 6. 시각화 6개 | 07–12 | 차례로 가격 히스토그램, 처리 전후 박스플롯, 세그먼트 막대그래프, 상관 히트맵, 구매일 수·금액 산점도, 월별 금액 라인차트 확인 |
| 7. 계산 확인과 인사이트 초안 | 13 | 계산 결과 검증, 인사이트 확인, README 결과 갱신 |

최종 실행 결과를 저장할 때는 다음 순서로 진행합니다.

1. 노트북의 커널이 현재 프로젝트 `.venv`인지 확인합니다.
2. **Restart Kernel**로 커널을 재시작합니다.
3. **Run All**로 모든 코드 셀을 실행합니다.
4. 마지막 셀의 검증·저장 완료 메시지를 확인합니다.
5. Windows는 `Ctrl+S`, Mac은 `Cmd+S`로 노트북을 저장합니다.

코드 셀은 총 **13개**입니다. 마지막 셀에서 `필수 계산 검증 통과`와 `전체 행 CSV 저장 확인: 3개`를 확인합니다.

마지막 셀은 이 README의 자동 갱신 영역에 실제 분석 결과를 기록합니다. 해당 영역의 시작·종료 주석을 유지해야 재실행 때 내용을 교체할 수 있습니다.

## 6. 전체 행을 확인하는 CSV

노트북에서는 요약표와 그래프를 읽고, 특정 거래나 고객의 상세 행을 찾을 때는 `outputs/`를 엽니다. 파일명 앞 두 숫자는 노트북의 큰 제목 번호입니다.

| 저장하는 코드 셀 | CSV 파일 | 현재 샘플 규모 | 볼 수 있는 내용 |
|---|---|---:|---|
| 02 · 데이터 로드 | [01_loaded_transactions.csv](outputs/01_loaded_transactions.csv) | 11,153행 × 12열 | 나이를 대치하고 피처를 만들기 전의 거래·상품·고객 정보 |
| 04 · IQR 탐지 | [03_cleaned_transactions.csv](outputs/03_cleaned_transactions.csv) | 11,153행 × 18열 | 대치한 나이, 이미지 평균·표준편차·누락 표시, 상품명 길이, 이상치 여부·처리 가격을 더한 거래 표 |
| 06 · RFM 계산 | [05_customer_rfm.csv](outputs/05_customer_rfm.csv) | 1,000행 × 8열 | 고객 한 명씩 R·F·M 값, 각 점수, 배정된 세그먼트 |

예를 들어 이상치 535건의 상세 내역은 `03_cleaned_transactions.csv`에서 `price_outlier`가 참인 행을 골라 확인합니다. 같은 행에서 `price`와 `price_iqr`를 비교하면 처리 전후 가격이 보입니다.

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

## 7. 다시 실행하기

**커널 재시작 → 모든 셀 실행 → 마지막 셀의 검증 결과 확인 → 노트북 저장** 순서로 진행합니다.

다시 실행하면 각 상세 CSV의 내용을 같은 이름의 파일에 덮어쓰고 노트북의 표·그래프·해석과 README의 자동 분석 결과 영역을 갱신합니다. 중간에 멈췄다면 마지막 셀까지 다시 실행해 모든 표가 같은 실행 결과인지 확인합니다.

이전 버전에서 만든 결과 38개가 있다면, 마지막 셀에서 이번 실행의 CSV 세 개를 확인한 뒤 이전 버전의 출력 파일명 35개만 정리합니다. 직접 보관할 파일에는 별도 이름을 사용하세요.

입력 파일 다섯 개는 다음 실행에서도 사용하므로 프로젝트 최상위에 그대로 둡니다.

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

3월과 9월은 일부 날짜만 포함되어 있으므로 전체 월과 같은 조건으로 비교하지 않습니다. 노트북의 월별 추세 그래프와 그 아래 해석에서 부분 관찰 월을 확인합니다.

분석 결과의 범위는 표본 고객 1,000명과 선택한 관찰 기간입니다. 전체 H&M 고객의 특성이나 실제 신규·이탈 여부로 바로 일반화하지 않습니다.

상관계수는 변수의 동반 변화를 나타내며, 인과관계를 증명하지 않습니다.

## 9. 실행 및 결과 검증

현재 샘플로 전체 실행을 마치면 아래 기준으로 확인할 수 있습니다.

| 확인 위치 | 확인 기준 |
|---|---|
| 환경 설정 셀 | 실행 중인 Python 경로와 NumPy·Pandas 버전 |
| 데이터 로드 단계 | 거래 11,153행, 원본 `price`와 분석용 `amount`가 일치 |
| RFM 단계 | 고객 1,000명을 5개 그룹으로 분류 |
| 시각화 단계 | 제목과 축 레이블이 있는 그래프 6개 |
| 마지막 코드 셀 | 행 수, 금액 보존, RFM 합계 등 필수 계산 검증 통과 |
| 프로젝트 README | 이번 실행에서 계산한 세그먼트 요약과 인사이트 3개 |

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
- 전체 행을 담은 상세 표: [outputs/](outputs/)
- Python 가상환경: [Python venv 문서](https://docs.python.org/3.12/library/venv.html)
- VS Code 노트북: [Jupyter Notebooks in VS Code](https://code.visualstudio.com/docs/datascience/jupyter-notebooks)
- VS Code 커널 선택: [Jupyter Kernel Management](https://code.visualstudio.com/docs/datascience/jupyter-kernel-management)

데이터 이용 조건은 `provenance.json`에 `Subject to Competition Rules`로 기록되어 있으며, 원본 대회의 이용 규정을 따릅니다.