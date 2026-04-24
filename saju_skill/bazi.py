"""Deterministic saju/BaZi helpers."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from lunar_python import Lunar, Solar

GAN_ELEMENTS = {
    "甲": ("목", "양"), "乙": ("목", "음"),
    "丙": ("화", "양"), "丁": ("화", "음"),
    "戊": ("토", "양"), "己": ("토", "음"),
    "庚": ("금", "양"), "辛": ("금", "음"),
    "壬": ("수", "양"), "癸": ("수", "음"),
}

ZHI_ELEMENTS = {
    "子": ("수", "양"), "丑": ("토", "음"), "寅": ("목", "양"), "卯": ("목", "음"),
    "辰": ("토", "양"), "巳": ("화", "음"), "午": ("화", "양"), "未": ("토", "음"),
    "申": ("금", "양"), "酉": ("금", "음"), "戌": ("토", "양"), "亥": ("수", "음"),
}

DAY_MASTER_TRAITS = {
    "甲": "큰 나무처럼 성장과 방향성이 강한 사람",
    "乙": "풀과 꽃처럼 유연하고 섬세하게 자라는 사람",
    "丙": "태양처럼 밝게 분위기를 여는 사람",
    "丁": "촛불처럼 집중력과 감성이 깊은 사람",
    "戊": "큰 산처럼 중심을 잡고 버티는 사람",
    "己": "밭흙처럼 현실적이고 돌봄이 강한 사람",
    "庚": "단단한 금속처럼 기준과 결단이 분명한 사람",
    "辛": "보석처럼 섬세한 기준과 완성도가 있는 사람",
    "壬": "큰 물처럼 생각과 이동성이 큰 사람",
    "癸": "비와 안개처럼 감각과 관찰이 섬세한 사람",
}


@dataclass(frozen=True)
class BirthDateTime:
    year: int
    month: int
    day: int
    hour: int
    minute: int


def build_bazi_context(user_info: dict[str, Any]) -> dict[str, Any]:
    birth = parse_birth(user_info.get("birth", ""), calendar=user_info.get("calendar"))
    if birth is None:
        return {"status": "unknown", "reason": "birth_parse_failed"}

    solar = Solar.fromYmdHms(birth.year, birth.month, birth.day, birth.hour, birth.minute, 0)
    lunar = solar.getLunar()
    eight = lunar.getEightChar()
    pillars = [
        _pillar("년주", eight.getYearGan(), eight.getYearZhi()),
        _pillar("월주", eight.getMonthGan(), eight.getMonthZhi()),
        _pillar("일주(나)", eight.getDayGan(), eight.getDayZhi()),
        _pillar("시주", eight.getTimeGan(), eight.getTimeZhi()),
    ]
    counts = _element_counts(pillars)
    day_gan = eight.getDayGan()
    day_zhi = eight.getDayZhi()
    strongest = sorted(counts.items(), key=lambda item: item[1], reverse=True)

    return {
        "status": "ok",
        "solar_datetime": f"{birth.year:04d}-{birth.month:02d}-{birth.day:02d} {birth.hour:02d}:{birth.minute:02d}",
        "lunar_date": str(lunar),
        "pillars_text": f"{eight.getYear()} {eight.getMonth()} {eight.getDay()} {eight.getTime()}",
        "pillars": pillars,
        "day_master": {
            "gan": day_gan,
            "zhi": day_zhi,
            "element": GAN_ELEMENTS.get(day_gan, ("", ""))[0],
            "yin_yang": GAN_ELEMENTS.get(day_gan, ("", ""))[1],
            "plain_trait": DAY_MASTER_TRAITS.get(day_gan, "자기만의 기준으로 삶을 풀어가는 사람"),
        },
        "element_counts": counts,
        "strong_elements": [name for name, _ in strongest[:2]],
        "weak_elements": [name for name, value in strongest if value == min(counts.values())],
        "interpretation_seeds": _interpretation_seeds(day_gan, counts),
    }


def parse_birth(text: str, calendar: str | None = None) -> BirthDateTime | None:
    normalized = text.replace(".", " ").replace("/", " ").replace("-", " ")
    solar_match = re.search(r"(?:양력|양)\s*(\d{2,4})\s*년?\s*(\d{1,2})\s*월?\s*(\d{1,2})", normalized)
    lunar_match = re.search(r"(?:음력|음)\s*(\d{2,4})\s*년?\s*(\d{1,2})\s*월?\s*(\d{1,2})", normalized)
    matches = list(re.finditer(r"(\d{2,4})\s*년?\s*(\d{1,2})\s*월?\s*(\d{1,2})", normalized))
    use_lunar = not solar_match and (calendar == "lunar" or lunar_match is not None)
    match = solar_match or lunar_match or (matches[-1] if matches else None)
    if match is None:
        return None
    year, month, day = [int(v) for v in match.groups()]
    if year < 100:
        year += 1900 if year >= 30 else 2000
    hour, minute = _parse_time(text)
    if use_lunar:
        try:
            solar = Lunar.fromYmdHms(year, month, day, hour, minute, 0).getSolar()
        except Exception:
            return None
        year = solar.getYear()
        month = solar.getMonth()
        day = solar.getDay()
        hour = solar.getHour()
        minute = solar.getMinute()
    return BirthDateTime(year=year, month=month, day=day, hour=hour, minute=minute)


def _parse_time(text: str) -> tuple[int, int]:
    match = re.search(r"(오전|오후)?\s*(\d{1,2})\s*시(?:\s*(\d{1,2})\s*분?)?", text)
    if not match:
        return 12, 0
    meridiem, hour_text, minute_text = match.groups()
    hour = int(hour_text)
    minute = int(minute_text or 0)
    if meridiem == "오후" and hour < 12:
        hour += 12
    if meridiem == "오전" and hour == 12:
        hour = 0
    return hour, minute


def _pillar(label: str, gan: str, zhi: str) -> dict[str, str]:
    gan_element, gan_yinyang = GAN_ELEMENTS.get(gan, ("", ""))
    zhi_element, zhi_yinyang = ZHI_ELEMENTS.get(zhi, ("", ""))
    return {
        "label": label,
        "gan": gan,
        "gan_element": gan_element,
        "gan_yinyang": gan_yinyang,
        "zhi": zhi,
        "zhi_element": zhi_element,
        "zhi_yinyang": zhi_yinyang,
        "pillar": f"{gan}{zhi}",
    }


def _element_counts(pillars: list[dict[str, str]]) -> dict[str, int]:
    counts = {"목": 0, "화": 0, "토": 0, "금": 0, "수": 0}
    for pillar in pillars:
        counts[pillar["gan_element"]] += 1
        counts[pillar["zhi_element"]] += 1
    return counts


def _interpretation_seeds(day_gan: str, counts: dict[str, int]) -> list[str]:
    seeds = [DAY_MASTER_TRAITS.get(day_gan, "자기 기준이 중요한 사람")]
    if counts.get("토", 0) >= 2:
        seeds.append("토가 있어 책임감, 지속력, 구조화 능력을 살리기 좋다")
    if counts.get("금", 0) >= 2:
        seeds.append("금이 살아 있어 판단, 정리, 계약, 규칙에 강점이 있다")
    if counts.get("수", 0) >= 2:
        seeds.append("수가 살아 있어 사고력, 정보 감각, 흐름 읽기에 강점이 있다")
    if counts.get("화", 0) <= 1:
        seeds.append("화가 약하면 표현, 홍보, 따뜻한 교류를 의식적으로 보완하면 좋다")
    if counts.get("목", 0) <= 1:
        seeds.append("목이 약하면 확장보다 계획된 성장과 꾸준한 학습이 중요하다")
    return seeds
