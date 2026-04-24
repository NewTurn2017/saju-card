---
name: saju-card
description: Collect Korean 사주 birth/profile details step by step and generate a single friendly Korean fortune-report card image via the `saju-card` CLI, using easy everyday wording, today/year guidance, a matching profile image, and deterministic Korean text overlay. Use when the user wants 사주, 운세, 오늘운세, 올해운세, or a one-page saju report card image.
license: MIT
metadata:
  version: 0.1.3
  author: genie
---

# saju-card

## When to use

Use this skill when the user wants a Korean 사주/운세/명리학 card image:
- one vertical info-card image, not a long multi-page report
- friendly fortune-app voice with simple everyday Korean
- today and year guidance without heavy 명리학 jargon
- a profile image that matches the reading mood
- readable Korean text embedded in the image
- Codex and Claude Code compatible local workflow

## User info flow

Collect missing information one item at a time. Use `?/N` for optional items: if the user answers `N`, `n`, or leaves it blank, skip that item.

1. 이름
2. 생년월일시: ask for date, time, calendar type, and whether it is 양력/음력 if not clear
3. 성별 or gender expression, if the user wants gendered reading
4. 출생지/timezone only if precision matters or the date is near midnight
5. 현재 주요 관심사 and up to 5 additional questions
6. Confirm: `이 정보로 사주 카드 이미지를 생성할까요? (Y/n)`

Do not invent missing required fields. If birth time is unknown, continue only after marking it as `출생시 미상` and make the card language less time-specific.

## Safety and tone

- Treat 사주 as cultural storytelling and self-reflection, not scientific certainty.
- Do not provide medical, legal, investment, or life-critical claims as facts.
- Avoid old-fashioned 무속인/만신 tone. Use bright, practical app-style language.
- Avoid hard terms unless needed; prefer plain words like "실행력", "관계", "오늘의 팁".
- Do not place technical notes, model/API wording, or calculation caveats inside the image.

## CLI usage

One-shot install:

```bash
curl -fsSL https://raw.githubusercontent.com/NewTurn2017/saju-card/main/install.sh | bash
```

If the CLI is installed:

```bash
saju-card
```

Non-interactive example:

```bash
saju-card \
  --name "김하늘" \
  --birth "1994년 3월 20일 오전 9시 30분, 양력, 서울" \
  --gender "여" \
  --question "올해 이직해도 괜찮을까?" \
  --question "연애운은 언제 좋아질까?" \
  --output ./out
```

From this source directory without installing:

```bash
uv run saju-card --name "김하늘" --birth "1994년 3월 20일 오전 9시 30분, 양력"
```

## Preconditions

1. `codex >= 0.121.0` is on PATH and `codex login status` succeeds with ChatGPT/OAuth.
2. `CODEX_API_KEY` is unset, because it overrides OAuth in `codex responses`.
3. `saju-card --version` succeeds, or run it through `uv run saju-card` from the skill repo.

## Expected result

The CLI prints one JSON object:

```json
{"job_id":"a1b2c3d4","output_dir":"/abs/out/a1b2c3d4","card":"/abs/out/a1b2c3d4/saju_card.png","plan_path":"/abs/out/a1b2c3d4/card_plan.json","input_path":"/abs/out/a1b2c3d4/input.json","elapsed_sec":120.0}
```

Show the user:
1. the absolute path to `saju_card.png`
2. the `job_id`
3. any caveat if the birth time/calendar was unknown

## Generation method

The CLI follows the `codex-sangpye` pattern:

1. call `codex responses` with `gpt-5.5` to create structured Korean card copy
2. call the `image_generation` tool through a chat orchestrator to create a vertical text-free background
3. generate a matching profile image
4. overlay all Korean text locally with Pillow for legibility
5. write `input.json`, `card_plan.json`, `profile.png`, `background.png`, and `saju_card.png`

Do not invoke this skill repeatedly for the same request unless the user asks for another version.
