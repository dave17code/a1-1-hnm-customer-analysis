# A1-1 · H&M 고객 구매 패턴 분석

기존 샘플 데이터 5개를 그대로 사용해 NumPy·Pandas로 데이터를 정리하고, Matplotlib·Seaborn으로 시각화하며, RFM으로 고객을 나누는 학습 프로젝트입니다. 보너스 과제는 포함하지 않습니다.

**진행 순서:** 코드 파일 추가 → 가상환경 생성 → 분석 도구 설치 → 노트북 커널 선택 → 셀별 분석 → 전체 재실행 확인 → GitHub에 코드와 결과 저장.

## 1. 현재 프로젝트에서 시작하기

VS Code의 **파일 → 폴더 열기**로 실제 클론한 `a1-1-hnm-customer-analysis` 폴더를 여세요. 로컬 폴더 이름을 `sample`로 유지했어도 괜찮습니다. 아래 파일 5개가 바로 보이는 폴더가 프로젝트 최상위입니다.

| 기존 파일 | 역할 | 확인된 입력 규모 |
|---|---|---|
| `transactions.csv` | 고객별 구매 기록 | 11,153행 |
| `customers.csv` | 고객의 나이·회원 상태 | 1,000명 |
| `articles.csv` | 상품명·종류·색상 | 6,055개 상품 |
| `images.npz` | 축소한 RGB 이미지 배열 | 6,047개, 각각 64×64×3 |
| `provenance.json` | 샘플 추출 조건과 개수 | 기간·선택 방법·누락 정보 |

데이터 파일은 **프로젝트 최상위에 유지**합니다. `data/sample` 폴더를 새로 만들거나 데이터를 다시 추출하지 않습니다. 분석 코드는 현재 구조에서 파일을 찾습니다.

VS Code에서 **터미널 → 새 터미널**을 열고 위치와 원격 주소를 확인하세요.

Windows PowerShell:

```powershell
Get-Location
git remote get-url origin
Get-ChildItem
```

Mac 터미널:

```bash
pwd
git remote get-url origin
ls
```

원격 주소는 `https://github.com/dave17code/a1-1-hnm-customer-analysis.git`이고, 위 표의 데이터 5개가 보여야 합니다.

## 2. 분석 코드 파일 4개 추가하기

제공된 `a1-1-hnm-analysis-setup.zip`을 다운로드 폴더에 저장하세요. 프로젝트 최상위에서 **처음 추가할 때 한 번** 아래 명령을 실행합니다.

Windows PowerShell:

```powershell
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\a1-1-hnm-analysis-setup.zip" -DestinationPath .
```

Mac:

```bash
unzip -n "$HOME/Downloads/a1-1-hnm-analysis-setup.zip" -d .
```

압축파일 최상위의 아래 4개 파일이 현재 프로젝트에 추가됩니다. 기존 데이터·`.gitignore`·Git 연결은 유지합니다. 다운로드 파일명이 바뀌었다면 명령의 ZIP 이름만 실제 이름으로 맞추세요.

| 추가 파일 | 하는 일 |
|---|---|
| `requirements.txt` | 설치할 분석 도구와 버전 목록 |
| `src/pipeline.py` | `DataAnalyzer` 클래스와 데이터 처리·계산 |
| `notebooks/analysis_report.ipynb` | 설명을 읽고 코드를 실행하며 표·그래프를 확인하는 분석 문서 |
| `README.md` | 지금 읽는 실행 가이드와 최종 인사이트 |

`requirements.txt`가 기존 `transactions.csv`와 **같은 위치**에 있어야 합니다. 압축파일 이름의 폴더를 한 겹 더 만들지 않습니다.

## 3. 각 컴퓨터에서 가상환경과 도구 설치하기

**Python 3.12가 설치된 환경을 기준으로 진행합니다.** Windows와 Mac에서 각각 `.venv`를 만들며, 다른 컴퓨터의 `.venv`를 복사하지 않습니다.

가상환경 안의 Python을 경로로 직접 실행하므로 활성화 명령이나 PowerShell 실행 정책 변경은 필요하지 않습니다.

### Windows PowerShell

```powershell
py -3.12 --version
py -3.12 -m venv .venv

.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -c "import sys, numpy, pandas, matplotlib, seaborn, ipykernel; print(sys.executable); print('분석 환경 준비 완료')"
```

`py`만 인식되지 않고 `python --version`이 **3.12.x**라면, 가상환경 생성 명령을 `python -m venv .venv`로 바꾸세요. 가상환경 생성 이후 명령은 그대로 사용합니다.

### Mac

```bash
python3.12 --version
python3.12 -m venv .venv

./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt

./.venv/bin/python -m pip check
./.venv/bin/python -c "import sys, numpy, pandas, matplotlib, seaborn, ipykernel; print(sys.executable); print('분석 환경 준비 완료')"
```

`python3.12`가 없지만 `python3 --version`이 **3.12.x**라면, 생성 명령을 `python3 -m venv .venv`로 바꿔도 됩니다. 3.12가 설치되지 않았다면 먼저 해당 버전의 Python을 준비하고 VS Code를 다시 여세요.

### 설치 완료 확인

- Python 버전 확인 결과가 `Python 3.12.x`입니다.
- `pip check` 결과가 `No broken requirements found.`입니다.
- 마지막 명령에 현재 프로젝트의 `.venv` 경로와 `분석 환경 준비 완료`가 출력됩니다.

| 도구 | 이번 프로젝트에서 사용하는 역할 |
|---|---|
| NumPy 2.3.5 | 이미지 배열의 평균·표준편차를 벡터 연산으로 계산 |
| Pandas 2.2.3 | CSV 읽기, 연결, 결측값 처리, 통계, RFM 집계 |
| Matplotlib 3.10.8 | 그래프 생성과 제목·축·범례 설정 |
| Seaborn 0.13.2 | 분포·상관관계·고객 비교 그래프 |
| IPyKernel | VS Code에서 노트북 코드를 실행하는 커널 |

NumPy·Pandas는 분석 도구이고, Matplotlib·Seaborn은 시각화에 사용합니다. IPyKernel은 실행 환경 도구입니다. 전체 `jupyter` 패키지를 추가로 설치하거나 브라우저용 Jupyter 서버를 실행할 필요는 없습니다.

## 4. VS Code에서 가상환경 선택하기

1. VS Code 확장에서 Microsoft의 **Python**과 **Jupyter**를 설치합니다.
2. 명령 팔레트를 엽니다. Windows는 `Ctrl+Shift+P`, Mac은 `Cmd+Shift+P`입니다.
3. **Python: Select Interpreter**를 실행하고 현재 프로젝트의 `.venv`를 선택합니다.
4. `notebooks/analysis_report.ipynb`를 엽니다.
5. 노트북 오른쪽 위 **Select Kernel → Select Another Kernel → Python Environments**에서 같은 `.venv`를 선택합니다. 화면에 `.venv`가 바로 보이면 바로 선택해도 됩니다.

실행 파일의 끝부분은 다음과 같습니다.

- Windows: `.venv\Scripts\python.exe`
- Mac: `.venv/bin/python`

선택 목록에 새 가상환경이 보이지 않으면 명령 팔레트의 **Developer: Reload Window**로 창을 다시 연 뒤 선택하세요. 노트북의 첫 실행 셀에 표시되는 Python 경로도 이 프로젝트의 `.venv`인지 확인합니다.

## 5. 노트북을 위에서 아래로 실행하기

처음에는 각 셀의 실행 버튼이나 `Shift+Enter`로 **한 셀씩** 실행하세요. 설명 → 코드 → 결과 순서로 읽으면서 다음 단계를 진행합니다. 중간 셀만 먼저 실행하면 앞에서 만든 변수가 없어 오류가 날 수 있습니다.

| 순서 | 실행 내용 | 확인할 것 |
|---|---|---|
| 1 | 데이터 로드·연결·기본 탐색 | 거래 11,153행이 유지되는지, 열과 자료형이 무엇인지 |
| 2 | 그룹별 결측값 처리 | 회원 상태별 나이 통계를 어떻게 계산하고 몇 명을 대치했는지 |
| 3 | 이미지·텍스트 특성 생성 | 이미지 평균·표준편차와 상품명 길이가 무엇을 뜻하는지 |
| 4 | IQR 이상치 탐지와 처리 | 경계값·탐지 건수, 원본 가격과 비교용 가격의 차이 |
| 5 | 기술통계 | 평균·중앙값·표준편차·사분위수와 각 통계의 관찰 단위 |
| 6 | RFM 계산과 고객 세분화 | R·F·M의 정의와 고객별 그룹 배정 기준 |
| 7 | 그래프 6개 | 제목·축·단위와 각 그래프 아래의 수치 해석 |
| 8 | 계산 검증과 인사이트 | 합계·행 수·그룹 수 검증, 실제 수치를 담은 인사이트 3개 |

노트북 마지막 셀은 아래 **분석 결과 구간만** 실행 결과로 갱신합니다. 결과 문장을 읽고 수치와 해석이 맞는지 검토하세요. 예상 효과는 검증할 가설이며, 이미 성과가 발생한 것처럼 표현하지 않습니다.

처음부터 끝까지 읽은 뒤 노트북의 **Restart Kernel**로 커널을 재시작하고 **Run All**로 전체 셀을 실행하세요. 오류 없이 끝나는지 확인한 다음 Windows는 `Ctrl+S`, Mac은 `Cmd+S`로 노트북을 저장합니다. 표·그래프 출력도 함께 저장됩니다.

완료 기준은 **필수 계산 검증 통과**, 그래프 **6개**, 실제 수치에 근거한 인사이트 **3개**입니다. 코드 실행과 별개로 본인이 각 결과의 의미를 설명할 수 있어야 합니다.

## 6. 분석할 때 지킬 해석 기준

- **한 행은 구매 기록 한 행**입니다. 고객 한 명이나 주문 한 건과 같지 않습니다. 같은 기록처럼 보이는 행도 근거 없이 삭제하지 않습니다.
- 고객 평균 나이는 고객별 한 행에서, 상품명 길이와 이미지 특성의 통계는 상품별 한 행에서 계산합니다. 거래 표에서 반복된 고객·상품 정보로 평균을 계산하면 구매가 잦은 대상을 더 많이 반영하게 됩니다.
- 관찰 기간은 **2020-03-23~2020-09-22**입니다. 약 6개월이지만 달력상으로는 **3월~9월의 7개 월**에 걸칩니다. 3월과 9월은 일부 날짜만 포함되므로 월별 합계를 비교할 때 관찰 일수도 함께 확인합니다.
- R은 기준일로부터 마지막 구매일까지 지난 일수, F는 **서로 다른 구매 날짜 수**, M은 원본 `price` 합계입니다. F를 정확한 주문·방문 횟수라고 부르거나 M을 원화·달러로 임의 환산하지 않습니다.
- 나이 결측값은 고객 표에서 그룹별 통계로 대치합니다. 원래 기록된 나이와 대치한 값의 차이는 전처리 기록으로 남깁니다.
- 이미지가 없는 상품 **8개**는 기존 샘플에 기록된 누락입니다. 그 상품의 거래는 유지하고 이미지 특성만 결측으로 표시합니다.
- 이미지 평균·표준편차는 **축소한 64×64 RGB 배열**의 값입니다. 배경·조명·포장도 포함되므로 상품 품질이나 구매 원인을 뜻한다고 단정하지 않습니다.
- IQR 비교용 가격은 별도 열로 처리합니다. RFM과 구매금액 합계에는 원본 가격을 사용합니다.
- 결과의 범위는 **선택한 기간에 구매한 표본 고객 1,000명**입니다. 전체 H&M 고객의 특성이나 확정적인 이탈·신규 가입 여부를 뜻하지 않습니다.

## 7. 코드와 실행 결과를 GitHub에 저장하기

기존 저장소를 그대로 사용합니다. `git init`이나 원격 주소 등록을 다시 하지 않습니다.

먼저 `.venv`가 제외되는지 확인하세요. Windows와 Mac에서 같은 Git 명령을 사용합니다.

```bash
git check-ignore .venv/pyvenv.cfg
git status --short
```

첫 명령이 `.venv/pyvenv.cfg`를 출력하면 제외 규칙이 적용된 것입니다. 아래에는 추가한 파일 4개만 명시적으로 등록합니다.

```bash
git add README.md requirements.txt src/pipeline.py notebooks/analysis_report.ipynb
git diff --cached --stat
git commit -m "Add A1-1 analysis environment and notebook"
git push
```

분석 실행 결과까지 저장했다면 노트북과 README가 함께 커밋됩니다. 환경 준비 단계에서 먼저 커밋했다면, 나중에 분석을 마친 후 변경된 README와 노트북을 다시 커밋하세요.

```bash
git add README.md notebooks/analysis_report.ipynb
git commit -m "Record A1-1 analysis results"
git push
```

두 번째 커밋은 실제 변경 내용이 있을 때 실행합니다. `.venv` 자체는 GitHub에 올리지 않습니다.

## 8. 다른 컴퓨터에서 이어서 작업하기

이미 클론한 프로젝트라면 해당 폴더에서 최신 파일을 받습니다.

```bash
git pull --ff-only
```

처음 받는 컴퓨터라면 원하는 작업 폴더에서 실행합니다.

```bash
git clone https://github.com/dave17code/a1-1-hnm-customer-analysis.git
cd a1-1-hnm-customer-analysis
```

그 컴퓨터에 가상환경이 없다면 **3단계의 해당 운영체제 명령**으로 `.venv`를 만들고 도구를 설치합니다. 이미 있다면 가상환경의 Python으로 `-m pip install -r requirements.txt`를 실행해 설치 목록을 반영합니다. 이후 **4단계에서 커널을 선택**하고 노트북을 실행합니다.

작업을 마칠 때 커밋·푸시하고, 다른 컴퓨터에서 작업을 시작할 때 `git pull --ff-only`로 받습니다. 기존 데이터의 재추출은 필요하지 않습니다.

## 검증 범위

첨부된 실제 샘플을 사용해 **Linux·Python 3.12.14의 IPython에서 코드 셀 13개를 순서대로 실행**했습니다. 그래프 6개, 인사이트 3개, 원본 파일 5개의 내용 보존과 RFM 합계를 확인했습니다. 공백·한글이 포함된 경로의 `notebooks` 폴더에서도 데이터 위치를 찾았습니다. Windows와 macOS의 설치 파일 제공 여부와 공식 실행 절차를 확인했으며, 사용자 컴퓨터의 VS Code 커널 실행은 위의 import 확인과 노트북 실행으로 점검합니다. 운영체제·폰트에 따라 그래프의 글꼴과 여백은 다를 수 있습니다.

## 분석 결과

<!-- ANALYSIS_RESULTS_START -->
아직 이 프로젝트에서 분석 결과를 기록하지 않았습니다. 노트북을 순서대로 실행하고 마지막 검증·기록 셀까지 완료하면 이 구간에 실제 수치와 인사이트가 작성됩니다.
<!-- ANALYSIS_RESULTS_END -->

## 출처와 공식 문서

- 원본 데이터: H&M Personalized Fashion Recommendations — https://www.kaggle.com/competitions/h-and-m-personalized-fashion-recommendations/data
- 샘플 추출 조건: 프로젝트의 `provenance.json`
- Python 가상환경: https://docs.python.org/3.12/library/venv.html
- VS Code 노트북: https://code.visualstudio.com/docs/datascience/jupyter-notebooks
- VS Code 커널 선택: https://code.visualstudio.com/docs/datascience/jupyter-kernel-management
- NumPy 2.3.5: https://pypi.org/project/numpy/2.3.5/
- Pandas 2.2.3: https://pypi.org/project/pandas/2.2.3/
- Matplotlib 3.10.8: https://pypi.org/project/matplotlib/3.10.8/
- Seaborn 0.13.2: https://pypi.org/project/seaborn/0.13.2/
