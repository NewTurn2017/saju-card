# saju-card

Codex와 Claude Code에서 사용할 수 있는 한국어 사주 포토카드 생성 스킬입니다.

`saju-card`는 사용자의 생년월일시를 받아 실제 사주 명식을 로컬에서 계산하고, `gpt-5.5`가 쉬운 한국어 사주 리포트 문구를 만든 뒤, 최종 세로형 포토카드 이미지 1장을 한 번에 생성합니다. 결과물에는 읽기 쉬운 한국어 텍스트, 사주에 맞춘 프로필 일러스트, 상황을 이해하기 쉬운 작은 만화 컷, 반짝이는 고급 실물 카드 스타일이 함께 들어갑니다.

## AI 에이전트 빠른 설치

Codex, Claude Code, 또는 다른 AI 코딩 에이전트가 사용자의 환경에 이 스킬을 설치해야 한다면 아래 명령부터 실행하세요.

```bash
curl -fsSL https://raw.githubusercontent.com/NewTurn2017/saju-card/main/install.sh | bash
```

설치 후 바로 확인합니다.

```bash
saju-card --version
saju-card --help
```

설치가 끝났는데 Codex나 Claude Code에서 스킬이 보이지 않으면, 사용자에게 Codex 또는 Claude Code를 재시작하라고 안내하세요.

## 설치 스크립트가 하는 일

`install.sh`는 다시 실행해도 안전합니다.

1. `uv` 설치 여부를 확인합니다.
2. `codex` CLI 설치 여부와 버전을 확인합니다.
3. `codex login status`로 ChatGPT/OAuth 로그인을 확인합니다.
4. `CODEX_API_KEY`가 설정되어 있으면 중단합니다.
5. `uv tool install`로 `saju-card` CLI를 전역 설치합니다.
6. Codex 스킬 파일을 등록합니다.
7. Claude Code 스킬 파일을 등록합니다.
8. `saju-card --help`로 기본 실행을 검증합니다.

등록 경로:

```text
~/.codex/skills/saju-card/SKILL.md
~/.codex/skills/saju-card/agents/openai.yaml
~/.claude/skills/saju-card/SKILL.md
~/.claude/skills/saju-card/agents/openai.yaml
```

## 필수 조건

설치 전에 아래 조건이 필요합니다.

- Python `>=3.11`
- `uv`
- Codex CLI `>=0.121.0`
- Codex ChatGPT/OAuth 로그인
- `CODEX_API_KEY` 미설정 상태

확인 명령:

```bash
uv --version
codex --version
codex login status
```

로그인이 안 되어 있으면:

```bash
codex login
```

`CODEX_API_KEY`가 설정되어 있으면 현재 셸에서 해제합니다.

```bash
unset CODEX_API_KEY
```

중요: Claude Code에서 이 스킬을 쓰더라도 내부 이미지 생성은 사용자의 Codex OAuth 세션을 통해 실행됩니다. 따라서 Claude Code 사용자도 `codex` CLI 로그인 상태가 필요합니다.

## Codex 또는 Claude Code에서 사용

설치 후 Codex나 Claude Code를 재시작한 뒤 이렇게 요청합니다.

```text
$saju-card 시작
```

스킬은 누락된 정보를 순서대로 물어봅니다.

1. 이름
2. 생년월일시
3. 양력/음력 여부
4. 성별 또는 젠더 표현
5. 출생지/timezone
6. 현재 관심사
7. 추가 질문 최대 5개
8. 최종 생성 확인

선택 항목은 `?/N` 형식으로 묻습니다. 사용자가 `N`, `n`, 또는 빈 답변을 주면 해당 항목은 건너뜁니다.

## CLI로 직접 사용

대화형 실행:

```bash
saju-card
```

비대화형 실행 예시:

```bash
saju-card \
  --name "장재현" \
  --birth "음력 1983년 12월 15일, 양력 1984년 1월 17일 오전 10시" \
  --calendar lunar \
  --gender "남자" \
  --birth-place "부산" \
  --interest "개발" \
  --interest "사업" \
  --interest "계약" \
  --interest "가족" \
  --output ./saju-output \
  --yes
```

실행 결과는 JSON 한 줄로 출력됩니다.

```json
{
  "job_id": "a1b2c3d4",
  "output_dir": "/abs/path/saju-output/a1b2c3d4",
  "card": "/abs/path/saju-output/a1b2c3d4/saju_card.png",
  "plan_path": "/abs/path/saju-output/a1b2c3d4/card_plan.json",
  "input_path": "/abs/path/saju-output/a1b2c3d4/input.json",
  "prompt_path": "/abs/path/saju-output/a1b2c3d4/card_prompt.txt",
  "background": null,
  "elapsed_sec": 120.0
}
```

AI 에이전트는 사용자에게 최소한 아래 정보를 알려주세요.

- 최종 이미지 경로: `saju_card.png`
- 작업 ID: `job_id`
- 생년월일시나 양력/음력 정보가 불확실했을 경우의 주의사항

## 수동 설치

보안 정책상 `curl | bash`를 사용할 수 없는 환경에서는 아래 순서로 설치합니다.

```bash
git clone https://github.com/NewTurn2017/saju-card.git
cd saju-card

uv tool install --reinstall "git+https://github.com/NewTurn2017/saju-card"

mkdir -p ~/.codex/skills/saju-card/agents
mkdir -p ~/.claude/skills/saju-card/agents

cp SKILL.md ~/.codex/skills/saju-card/SKILL.md
cp agents/openai.yaml ~/.codex/skills/saju-card/agents/openai.yaml

cp SKILL.md ~/.claude/skills/saju-card/SKILL.md
cp agents/openai.yaml ~/.claude/skills/saju-card/agents/openai.yaml

saju-card --version
```

## 업데이트

가장 쉬운 업데이트 방법은 설치 스크립트를 다시 실행하는 것입니다.

```bash
curl -fsSL https://raw.githubusercontent.com/NewTurn2017/saju-card/main/install.sh | bash
```

CLI만 다시 설치하려면:

```bash
uv tool install --reinstall "git+https://github.com/NewTurn2017/saju-card"
```

스킬 파일까지 업데이트했다면 Codex 또는 Claude Code를 재시작하세요.

## 결과 이미지 스타일

기본 결과물은 한 장짜리 완성 이미지입니다.

- 세로형 프리미엄 사주 포토카드
- 실물 카드처럼 보이는 라미네이팅 광택
- 은은한 홀로그램 박, 펄, 반짝임
- 카드 안에 직접 렌더링되는 한국어 텍스트
- 한자 명식표를 전면에 내세우지 않는 쉬운 해석
- 사주 기질에 맞춘 프로필 일러스트
- 개발, 계약, 가족, 오늘의 실행 팁 같은 상황 만화 컷
- MZ, 직장인, 주부, 학생이 모두 이해할 수 있는 쉬운 말투

## 내부 동작

1. 사용자의 생년월일시 문장을 파싱합니다.
2. 음력 정보가 있으면 양력으로 변환합니다.
3. `lunar-python`으로 실제 사주 명식을 계산합니다.
4. `gpt-5.5`가 명식 기반 한국어 카드 문구를 작성합니다.
5. 카드 문구를 긴 최종 이미지 프롬프트로 변환합니다.
6. 이미지 생성 도구를 한 번 호출해 완성 이미지를 만듭니다.
7. 결과 파일을 저장합니다.

저장 파일:

```text
input.json
card_plan.json
card_prompt.txt
saju_card.png
```

`--no-bg-image`는 로컬 디버그용 fallback입니다. 기본 흐름은 최종 카드 이미지 1회 생성입니다.

## AI 에이전트용 문제 해결

### `uv not found`

macOS라면:

```bash
brew install uv
```

이후 설치 스크립트를 다시 실행합니다.

### `codex CLI not found`

Codex CLI를 설치하거나 최신 버전으로 업데이트합니다.

```bash
npm install -g @openai/codex@latest
```

### `codex login status failed`

사용자가 ChatGPT/OAuth로 로그인해야 합니다.

```bash
codex login
codex login status
```

### `CODEX_API_KEY is set`

현재 셸에서 해제한 뒤 다시 실행합니다.

```bash
unset CODEX_API_KEY
```

### 스킬은 설치됐는데 보이지 않음

Codex 또는 Claude Code를 재시작한 뒤 다시 시도합니다.

```text
$saju-card 시작
```

### 이미지 생성이 오래 걸림

긴 한국어 텍스트와 여러 일러스트를 포함한 고해상도 카드라 시간이 걸릴 수 있습니다. CLI timeout 전에 임의로 중단하지 마세요.

### 결과 텍스트나 디자인이 마음에 들지 않음

같은 입력으로 다시 실행할 수 있습니다. 생성에 사용된 자료는 아래 파일에 남습니다.

```text
card_plan.json
card_prompt.txt
```

AI 에이전트는 이 두 파일을 확인한 뒤 문구나 프롬프트 방향을 조정해 다시 생성하면 됩니다.

## 개발자 검증

소스 디렉터리에서 실행:

```bash
uv run saju-card --version
uv run saju-card --help
```

배포 전 검증:

```bash
uv run python -m compileall saju_skill
uv run --with pyyaml python /Users/genie/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
uv build
git diff --check
```

빌드 산출물은 `dist/`에 저장됩니다. 생성된 카드는 기본적으로 `saju-output/`에 저장됩니다.

## 최신 릴리즈

- https://github.com/NewTurn2017/saju-card/releases/tag/v0.2.0

최신 `main` 기준 설치:

```bash
uv tool install --reinstall "git+https://github.com/NewTurn2017/saju-card"
```

## 안전 원칙

이 프로젝트는 사주를 문화적 스토리텔링과 자기 성찰 도구로 다룹니다. 의료, 법률, 투자, 생명 안전처럼 중요한 결정을 사실처럼 단정하지 않습니다.
