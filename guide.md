# 🛍️ A1-1 H&M 단골 고객 분석 실행 가이드

대상 프로젝트는 `a1-1-hnm-customer-analysis`이며, 실행할 파일은 `notebooks/analysis_report.ipynb`입니다. ZIP에는 분석용 표본, 상품 사진 배열, 실행 결과가 들어 있습니다. 내 컴퓨터에서 결과를 다시 계산하려면 아래 순서로 진행하세요.

## 1. 📂 VS Code에서 프로젝트 폴더 열기

1. ZIP을 풀고 VS Code의 `File → Open Folder…`로 `a1-1-hnm-customer-analysis` 폴더를 여세요. 이미 같은 버전의 프로젝트를 열어 뒀다면 그대로 사용하세요.
2. 왼쪽 탐색기에서 `requirements.txt`, `pyproject.toml`, `analysis_input.csv`, `images.npz`, `notebooks/`가 함께 보이는지 확인하세요. 같은 이름의 폴더가 두 겹이면 이 파일들이 있는 안쪽 폴더를 여세요.
3. 왼쪽 확장 메뉴에서 Microsoft의 `Python`과 `Jupyter` 확장을 설치하세요. 설치돼 있다면 다음 단계로 가세요.
4. `Terminal → New Terminal`을 여세요. Windows에서는 터미널 패널 오른쪽의 프로필 메뉴에서 `Git Bash`를 열고, 아이맥에서는 `zsh`를 사용하세요.

## 2. 🧰 Python 3.12 가상환경과 분석 도구 준비

`.venv`는 이 프로젝트가 쓸 Python과 도구를 두는 폴더입니다. 아래에서 내 운영체제와 현재 상태에 맞는 블록 하나를 실행하세요. 각 블록은 통째로 붙여넣어도 됩니다.

### Windows · Git Bash

새로 압축을 풀었고 이 폴더에 `.venv`가 없을 때

```bash
py -3.12 -m venv .venv &&
source .venv/Scripts/activate &&
python -m pip install -r requirements.txt
```

현재 프로젝트에 Windows용 Python 3.12 가상환경이 이미 있을 때

```bash
source .venv/Scripts/activate &&
python -m pip install -r requirements.txt
```

첫 명령에서 Python 3.12를 찾을 수 없다는 메시지가 나오면 Windows에 Python 3.12를 설치하고 새 Git Bash 터미널을 여세요. `py -3.12 --version`에서 `Python 3.12.x`가 표시되면 위 명령을 진행할 수 있습니다.

### 아이맥 · zsh

새로 압축을 풀었고 이 폴더에 `.venv`가 없을 때

```bash
python3.12 -m venv .venv &&
source .venv/bin/activate &&
python3 -m pip install -r requirements.txt
```

`python3.12`를 찾지 못하면 `python3 --version`을 확인하세요. 3.12.x라면 첫 줄의 `python3.12`를 `python3`로 바꿔 실행하세요. 교육장 아이맥에 3.9 등 다른 버전만 있다면 아래 방법으로 프로젝트용 Python 3.12를 준비할 수 있습니다.

1. `uv --version`으로 uv를 확인하세요. 명령을 찾지 못하면 다음 두 줄로 공식 설치 프로그램을 실행하고 이 터미널의 경로를 설정하세요.

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   export PATH="$HOME/.local/bin:$PATH"
   ```

2. 프로젝트 폴더에서 아래를 실행하세요.

   ```bash
   uv python install 3.12 &&
   uv venv --seed --python 3.12 .venv &&
   source .venv/bin/activate &&
   python3 -m pip install -r requirements.txt
   ```

현재 프로젝트에 아이맥용 Python 3.12 가상환경이 이미 있을 때

```bash
source .venv/bin/activate &&
python3 -m pip install -r requirements.txt
```

예전에 uv로 만든 환경에서 `No module named pip`가 나오면 같은 프로젝트 폴더에서 `uv pip install --python .venv/bin/python -r requirements.txt`를 실행하세요.

### 설치 결과 확인

가상환경을 활성화한 터미널에서 실행하세요. Windows는 `python`, 아이맥은 `python3`를 사용하면 됩니다.

```bash
python -c "import sys, numpy, pandas, hnm_analysis; print(sys.version.split()[0]); print(sys.executable); print(hnm_analysis.__file__)"
```

첫 줄은 `3.12.x`, 둘째 줄은 현재 프로젝트의 `.venv` 안에 있는 Python, 셋째 줄은 현재 프로젝트의 `src/__init__.py` 경로여야 합니다. `requirements.txt` 마지막 줄의 `-e .`는 프로젝트 안의 분석 코드를 `hnm_analysis`라는 이름으로 불러올 수 있게 합니다. 기존 프로젝트에 새 파일을 덮어쓴 경우에도 이번에는 설치 명령을 한 번 실행하세요.

## 3. 🔌 노트북 커널 연결

1. 왼쪽 탐색기에서 `notebooks → analysis_report.ipynb`를 여세요.
2. 노트북 오른쪽 위의 `Select Kernel` 또는 현재 보이는 커널 이름을 누르세요.
3. 목록에서 현재 프로젝트의 `.venv (Python 3.12.x)`를 선택하세요. 첫 목록에 없으면 `Select Another Kernel… → Python Environments…`를 여세요.
4. 같은 이름이 여럿이면 실행 파일의 경로를 확인하세요. Windows는 이 프로젝트의 `.venv\Scripts\python.exe`, 아이맥은 `.venv/bin/python`을 선택하면 됩니다.

터미널에서 `activate`를 실행하면 그 터미널의 Python이 정해집니다. 노트북의 `Select Kernel`은 셀의 코드를 실행할 Python을 정합니다. 셀 01에서 `numpy` 또는 `hnm_analysis`를 찾을 수 없다고 하면 2단계에 표시한 실행 파일 경로와 선택한 커널의 경로부터 맞춰 보세요.

## 4. ▶️ 셀 7개 실행하고 저장하기

1. 이전 셀을 실행했거나 파일을 교체했다면 노트북 상단에서 `Restart Kernel`을 누르세요. 새 커널을 처음 연 경우에는 바로 다음 단계로 가세요.
2. 상단의 `Run All`을 한 번 누르세요. 셀 01이 불러온 거래표를 다음 셀이 이어받으므로 위에서 아래로 실행합니다.
3. 이번 실행이 셀 07까지 끝나고 `검증 완료`, `README 분석 결과 갱신 완료`가 출력됐는지 확인하세요. ZIP을 처음 열 때 보이는 표와 그림은 이미 저장돼 있던 결과입니다.
4. Windows는 `Ctrl + S`, 아이맥은 `Cmd + S`로 저장하세요. 이번 실행에서 표시된 표·그래프와 설명이 노트북 파일에 저장됩니다.

## 5. 📊 셀마다 무엇을 확인하면 될까요?

| 셀 | 화면과 파일에서 확인할 내용 |
|---|---|
| 01 · 거래 읽기 | 첫 5행과 자료형이 표시됩니다. 출발점은 거래 11,153행 × 입력 8열입니다. |
| 02 · 결측치와 상품 특성 | 고객의 빈 나이·회원 상태를 처리하고 상품명 길이, 사진 평균·표준편차를 거래표에 붙입니다. |
| 03 · 이상치 탐지 | 금액 경계를 벗어난 거래 535행을 확인합니다. 원본 금액을 보존한 전체 거래 11,153행 × 11열을 `outputs/03_cleaned_transactions.csv`에 저장합니다. |
| 04 · 기술통계 | 거래금액은 거래별, 나이는 고객별, 상품 특성은 상품별로 요약합니다. 각 표에서 평균과 중앙값을 확인할 수 있습니다. |
| 05 · 단골 분류 | 고객 1,000명의 최근 구매 시점·구매일 수·누적금액으로 5개 그룹을 만듭니다. 고객당 한 행인 결과를 `outputs/05_customer_rfm.csv`에 저장합니다. |
| 06 · 시각화 | 셀 아래에 히스토그램, 박스플롯, 막대그래프, 스피어만 순위상관 히트맵, 산점도, 월별 라인차트가 표시됩니다. |
| 07 · 검증과 제안 | 거래 수와 금액 합계, 6종 차트, CSV 2개 등을 검증하고 `README.md`의 비즈니스 제안 3가지를 갱신합니다. |

다음에 같은 컴퓨터의 같은 프로젝트에서 다시 분석할 때는 노트북을 열고 연결된 커널을 확인한 뒤 `Restart Kernel → Run All → 저장`하면 됩니다. 셀 03과 05가 같은 경로에 CSV를 덮어쓰므로 기존 결과를 미리 지울 필요가 없습니다. 새 컴퓨터에 프로젝트를 옮겼다면 그 컴퓨터에서 2~3단계를 다시 진행하세요.

[VS Code 노트북 커널 공식 안내](https://code.visualstudio.com/docs/datascience/jupyter-kernel-management) · [uv 설치 안내](https://docs.astral.sh/uv/getting-started/installation/) · [uv로 Python 버전 설치](https://docs.astral.sh/uv/guides/install-python/)
