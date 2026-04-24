"""CLI entry point for the saju-card skill."""
from __future__ import annotations

import argparse
import json
import secrets
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from saju_skill import __version__
from saju_skill.bazi import build_bazi_context
from saju_skill.codex_client import CodexAuthError, CodexCallError, CodexClient, write_bytes
from saju_skill.prompts import (
    DEFAULT_SIZE,
    FINAL_CARD_IMAGE_INSTRUCTIONS,
    MODEL,
    SAJU_PLAN_SYSTEM_PROMPT,
    build_final_card_prompt,
)
from saju_skill.renderer import render_card

EXIT_OK = 0
EXIT_AUTH = 1
EXIT_INPUT = 2
EXIT_API = 3
EXIT_FS = 4


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    t0 = time.time()

    try:
        user_info = _collect_user_info(args)
        output_dir, job_id = _prepare_output(args)
    except (ValueError, OSError) as e:
        _stderr(f"error: {e}")
        return EXIT_INPUT

    input_path = output_dir / "input.json"
    plan_path = output_dir / "card_plan.json"
    prompt_path = output_dir / "card_prompt.txt"
    card_path = output_dir / "saju_card.png"

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        input_path.write_text(json.dumps(user_info, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as e:
        _stderr(f"error (filesystem): {e}")
        return EXIT_FS

    try:
        _stderr("준비 상태 확인 중...")
        client = CodexClient(codex_bin=args.codex_bin)
        _stderr("      OK")
        _stderr("      [1/2] 사주 보고서 내용 정리 중...")
        plan = _build_plan(client, user_info, model=args.model)
        plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        prompt = build_final_card_prompt(plan, user_info, size=tuple(args.size))
        prompt_path.write_text(prompt, encoding="utf-8")

        if args.no_bg_image:
            _stderr("      [2/2] 이미지 생성 생략: 로컬 확인용 카드 렌더링")
            render_card(
                plan,
                card_path,
                background_path=None,
                size=tuple(args.size),
            )
        else:
            _stderr("      [2/2] 완성 사주 포토 카드 이미지 생성 중...")
            card_bytes = client.generate_image(
                orchestrator_model=args.model,
                prompt=prompt,
                size=tuple(args.size),
                quality=args.quality,
                instructions=FINAL_CARD_IMAGE_INSTRUCTIONS,
            )
            write_bytes(card_path, card_bytes)
    except CodexAuthError as e:
        _stderr(f"error: {e}")
        return EXIT_AUTH
    except CodexCallError as e:
        _stderr(f"error (codex): {e}")
        return EXIT_API
    except OSError as e:
        _stderr(f"error (filesystem): {e}")
        return EXIT_FS
    except Exception as e:  # noqa: BLE001 - CLI should return stable codes.
        _stderr(f"error: {e}")
        return EXIT_API

    elapsed = round(time.time() - t0, 1)
    payload = {
        "job_id": job_id,
        "output_dir": str(output_dir),
        "card": str(card_path),
        "plan_path": str(plan_path),
        "input_path": str(input_path),
        "prompt_path": str(prompt_path),
        "background": None,
        "elapsed_sec": elapsed,
    }
    print(json.dumps(payload, ensure_ascii=False))
    return EXIT_OK


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="saju-card",
        description="Generate one friendly Korean saju report image.",
    )
    parser.add_argument("--version", action="version", version=f"saju-card {__version__}")
    parser.add_argument("--name", help="이름")
    parser.add_argument("--birth", help="생년월일시. 예: 1994년 3월 20일 오전 9시 30분, 양력, 서울")
    parser.add_argument("--gender", help="성별 또는 젠더 표현")
    parser.add_argument("--calendar", choices=["solar", "lunar", "unknown"], help="양력/음력")
    parser.add_argument("--birth-place", help="출생지 또는 timezone")
    parser.add_argument("--interest", action="append", default=[], help="현재 주요 관심사")
    parser.add_argument("--question", action="append", default=[], help="추가 질문. 최대 5개까지 반복")
    parser.add_argument("--output", default="./saju-output", metavar="DIR", help="Parent output directory")
    parser.add_argument("--job-id", default=None, help="Override the generated job id")
    parser.add_argument("--quality", choices=["standard", "high"], default="high")
    parser.add_argument("--model", default=MODEL, help=f"Codex responses model (default: {MODEL})")
    parser.add_argument("--codex-bin", default="codex", help="Path to codex CLI")
    parser.add_argument("--size", nargs=2, type=int, default=list(DEFAULT_SIZE), metavar=("W", "H"))
    parser.add_argument("--no-bg-image", action="store_true", help="Use local visual style without generated images")
    parser.add_argument("--yes", action="store_true", help="Skip final interactive confirmation")
    return parser


def _collect_user_info(args: argparse.Namespace) -> dict[str, Any]:
    if not args.no_bg_image and any(value % 16 != 0 for value in args.size):
        raise ValueError("--size values must both be divisible by 16")

    interactive = sys.stdin.isatty()
    name = args.name or (_ask_required("이름") if interactive else None)
    birth = args.birth or (_ask_required("생년월일시 (예: 1994년 3월 20일 오전 9시 30분, 양력)") if interactive else None)
    if not name:
        raise ValueError("--name is required in non-interactive mode")
    if not birth:
        raise ValueError("--birth is required in non-interactive mode")

    calendar = args.calendar
    if not calendar and interactive:
        raw = _ask_optional("양력/음력/모름 (?/N, 기본=양력)")
        calendar = _calendar_value(raw) if raw else "solar"
    calendar = calendar or "unknown"

    gender = args.gender
    if gender is None and interactive:
        gender = _ask_optional("성별 또는 젠더 표현 (?/N)")

    birth_place = args.birth_place
    if birth_place is None and interactive:
        birth_place = _ask_optional("출생지/timezone (?/N)")

    interests = list(args.interest or [])
    if interactive and not interests:
        raw = _ask_optional("현재 주요 관심사 (?/N)")
        if raw:
            interests.append(raw)

    questions = list(args.question or [])[:5]
    if interactive:
        while len(questions) < 5:
            raw = _ask_optional(f"추가 질문 {len(questions) + 1} (?/N)")
            if not raw:
                break
            questions.append(raw)

    user_info = {
        "name": name.strip(),
        "birth": birth.strip(),
        "calendar": calendar,
        "gender": (gender or "").strip() or None,
        "birth_place": (birth_place or "").strip() or None,
        "interests": [v.strip() for v in interests if v.strip()],
        "questions": [v.strip() for v in questions if v.strip()][:5],
        "report_date": datetime.now().strftime("%Y-%m-%d"),
        "tone": "friendly fortune app + easy Korean + no technical wording",
        "bazi": build_bazi_context({"birth": birth.strip(), "calendar": calendar}),
    }

    if interactive and not args.yes:
        _stderr(json.dumps(user_info, ensure_ascii=False, indent=2))
        confirm = input("이 정보로 사주 카드 이미지를 생성할까요? (Y/n) ").strip().lower()
        if confirm in {"n", "no", "아니오", "아니요"}:
            raise ValueError("cancelled by user")
    return user_info


def _prepare_output(args: argparse.Namespace) -> tuple[Path, str]:
    job_id = args.job_id or secrets.token_hex(4)
    output_root = Path(args.output).expanduser().resolve()
    return output_root / job_id, job_id


def _build_plan(client: CodexClient, user_info: dict[str, Any], *, model: str) -> dict[str, Any]:
    user_text = (
        "다음 사용자 정보와 계산된 사주 명식을 바탕으로 사주 보고서용 JSON을 만들어라. "
        "명식은 반드시 bazi 값을 기준으로 해석하고, 추측으로 다른 명식을 만들지 마라. "
        "반드시 json object만 반환해라.\n"
        + json.dumps(user_info, ensure_ascii=False, indent=2)
    )
    raw = client.call_responses(
        model=model,
        instructions=SAJU_PLAN_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": [{"type": "input_text", "text": user_text}]}],
        response_format={"type": "json_object"},
    )
    plan = _parse_json_object(raw)
    return _normalize_plan(plan, user_info)


def _parse_json_object(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start < 0 or end < start:
            raise
        data = json.loads(raw[start : end + 1])
    if not isinstance(data, dict):
        raise ValueError("model returned JSON that is not an object")
    return data


def _normalize_plan(plan: dict[str, Any], user_info: dict[str, Any]) -> dict[str, Any]:
    plan.setdefault("title", f"{user_info['name']}님의 사주 보고서")
    plan.setdefault("subtitle", "내가 가진 기질과 오늘/올해의 흐름")
    plan.setdefault("birth_line", user_info["birth"])
    plan.setdefault("core_keywords", ["균형", "전환", "성장"])
    plan.setdefault("question_answers", [])
    plan.setdefault("profile", {
        "badge": "기준을 세우고 기회를 만드는 타입",
        "archetype": "실행형 리더",
        "avatar_prompt": "",
    })
    plan.setdefault("closing", {
        "summary": "꾸준함과 신뢰를 바탕으로 좋은 흐름을 키우는 타입이에요.",
        "lucky_colors": ["#111111", "#D8B978", "#4E86B7", "#5FA66B"],
        "lucky_keywords": ["신뢰", "성장", "실행", "균형"],
        "footer": "오늘의 작은 선택이 내일의 운을 만들어요.",
    })
    _apply_bazi(plan, user_info.get("bazi") or {})
    return plan


def _apply_bazi(plan: dict[str, Any], bazi: dict[str, Any]) -> None:
    if bazi.get("status") != "ok":
        return
    pillars = bazi.get("pillars") or []
    by_label = {p.get("label"): p for p in pillars if isinstance(p, dict)}
    order = ["시주", "일주(나)", "월주", "년주"]
    grid = []
    for label in order:
        p = by_label.get(label) or {}
        grid.append({
            "label": label,
            "top": p.get("gan", "?"),
            "top_element": p.get("gan_element", ""),
            "bottom": p.get("zhi", "?"),
            "bottom_element": p.get("zhi_element", ""),
        })
    plan["saju_grid"] = grid
    day = bazi.get("day_master") or {}
    if day:
        keywords = _day_keywords(day.get("gan", ""), bazi.get("element_counts") or {})
        plan["day_master"] = f"일간(나): {day.get('gan', '?')}{day.get('zhi', '')} | 성향 키워드: {keywords}"
    counts = bazi.get("element_counts") or {}
    if counts:
        labels = {"목": "성장", "화": "표현", "토": "중심", "금": "판단", "수": "지혜"}
        plan["elements"] = [
            {"name": name, "score": int(counts.get(name, 0)), "label": labels[name]}
            for name in ["목", "화", "토", "금", "수"]
        ]


def _day_keywords(day_gan: str, counts: dict[str, Any]) -> str:
    base = {
        "甲": "성장, 추진, 방향성",
        "乙": "유연함, 감각, 관계",
        "丙": "표현, 활력, 확장",
        "丁": "집중, 감성, 섬세함",
        "戊": "안정, 책임, 중심",
        "己": "현실감, 돌봄, 조율",
        "庚": "판단, 결단, 구조화",
        "辛": "완성도, 기준, 섬세함",
        "壬": "사고력, 이동, 흐름",
        "癸": "관찰, 감각, 지혜",
    }.get(day_gan, "기준, 실행, 균형")
    if int(counts.get("금", 0) or 0) >= 2:
        return "판단력, 계약감, 구조화"
    if int(counts.get("토", 0) or 0) >= 2:
        return "책임감, 안정감, 실행력"
    return base


def _ask_required(label: str) -> str:
    while True:
        value = input(f"{label}: ").strip()
        if value:
            return value
        print("필수 항목입니다.", file=sys.stderr)


def _ask_optional(label: str) -> str | None:
    value = input(f"{label}: ").strip()
    if not value or value.lower() in {"n", "no"}:
        return None
    return value


def _calendar_value(raw: str | None) -> str:
    if not raw:
        return "unknown"
    raw = raw.strip().lower()
    if raw in {"양력", "solar", "s"}:
        return "solar"
    if raw in {"음력", "lunar", "l"}:
        return "lunar"
    return "unknown"


def _stderr(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
