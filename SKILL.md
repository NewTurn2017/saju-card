---
name: saju-card
description: Collect Korean 사주 birth/profile details step by step, calculate the actual four pillars, and generate one premium glossy Korean saju photo-card image via the `saju-card` CLI, using easy everyday wording, today/year guidance, a built-in profile illustration, small situational cartoon cuts, and one-shot final image generation. Use when the user wants 사주, 운세, 오늘운세, 올해운세, or a one-page saju report card image.
license: MIT
metadata:
  version: 0.2.0
  author: genie
---

# saju-card

## When to use

Use this skill when the user wants a Korean 사주/운세/명리학 card image:
- one vertical info-card image, not a long multi-page report
- friendly fortune-app voice with simple everyday Korean
- today and year guidance without heavy 명리학 jargon
- one premium glossy physical photo-card style image
- one built-in profile illustration plus small situational cartoon cuts
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
- Calculate the four pillars first and base the reading on that result.
- Do not foreground 한자 명식표 in the final card. Use the calculated 명식 internally, then explain it in plain Korean.
- Prefer premium glossy photo-card visuals: laminated shine, subtle holographic foil, sparkles, and crisp Korean typography.

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

1. calculate the user's four pillars locally
2. call `codex responses` with `gpt-5.5` as a top-tier saju reader to create structured Korean card copy from that calculation
3. turn that copy into one detailed final-image prompt
4. call the `image_generation` tool once to create the finished vertical card, including Korean text, profile illustration, sparkles, and small contextual cartoon cuts
5. write `input.json`, `card_plan.json`, `card_prompt.txt`, and `saju_card.png`

`--no-bg-image` is a local fallback/debug mode only. The default path should be one-shot final image generation, not separate profile generation or local text compositing.

Do not invoke this skill repeatedly for the same request unless the user asks for another version.
