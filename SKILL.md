---
name: saju-card
description: Collect Korean 사주 birth/profile details step by step and generate a single vertical MZ-premium Korean 사주 info card image via the `saju-card` CLI, using Codex OAuth `codex responses` plus image_generation with deterministic Korean text overlay. Use when the user wants 사주, 운세, 명리학, 대만신 스타일 풀이, or a one-page saju report card image.
license: MIT
metadata:
  version: 0.1.0
  author: genie
---

# saju-card

## When to use

Use this skill when the user wants a Korean 사주/운세/명리학 card image:
- one vertical info-card image, not a long multi-page report
- warm "대만신" voice with MZ-friendly copy
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
- Keep the "대만신" tone warm, vivid, and authoritative, but avoid fear-based wording.
- Explain hard terms simply: `비견(쉽게 말해 내 편이자 경쟁자인 친구 기운)`.
- If exact 명식 calculation cannot be guaranteed from the supplied data, label it as `간이 명식` or `정밀 보정 필요`.

## CLI usage

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
3. overlay all Korean text locally with Pillow for legibility
4. write `input.json`, `card_plan.json`, `background.png`, and `saju_card.png`

Do not invoke this skill repeatedly for the same request unless the user asks for another version.
