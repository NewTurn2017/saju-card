"""Pillow renderer for the final Korean saju report card."""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageFilter

WIDTH = 1472
HEIGHT = 1856

FONT_CANDIDATES = [
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
    "/System/Library/Fonts/Supplemental/NotoSansCJK-Regular.ttc",
    "/Library/Fonts/NanumGothic.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
]

ELEMENT_COLORS = {
    "목": "#74A66A",
    "화": "#E28B72",
    "토": "#D8B978",
    "금": "#9AA1A8",
    "수": "#78A3C8",
}

ICON_LABELS = {
    "mountain": "△",
    "target": "◎",
    "crown": "♕",
    "heart": "♡",
    "leaf": "☘",
    "rocket": "⌁",
    "tree": "♧",
    "star": "★",
}


def render_card(
    plan: dict[str, Any],
    output_path: Path,
    *,
    background_path: Path | None = None,
    avatar_path: Path | None = None,
    size: tuple[int, int] = (WIDTH, HEIGHT),
) -> Path:
    width, height = size
    palette = _palette(plan)
    image = _load_background(background_path, size, palette)
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    fonts = FontSet()

    m = 38
    gap = 24
    left_w = 470
    right_x = m + left_w + gap
    right_w = width - right_x - m
    col_w = (right_w - gap) // 2
    right_col_x = right_x + col_w + gap

    _draw_profile(overlay, draw, plan, (m, 38, m + left_w, 690), fonts, palette, avatar_path)
    _draw_saju_grid(draw, plan, (right_x, 38, width - m, 515), fonts, palette)
    _draw_personality(draw, plan, (m, 725, m + left_w, 1280), fonts, palette)
    _draw_elements(draw, plan, (right_x, 545, right_x + col_w, 980), fonts, palette)
    _draw_fortune_flow(draw, plan, (right_col_x, 545, width - m, 1280), fonts, palette)
    _draw_recommendations(draw, plan, (m, 1315, m + left_w, 1745), fonts, palette)
    _draw_relationship(draw, plan, (right_x, 1010, right_x + col_w, 1745), fonts, palette)
    _draw_closing(draw, plan, (right_col_x, 1315, width - m, 1745), fonts, palette)
    _draw_footer(draw, plan, (m, 1776, width - m, height - 24), fonts, palette)

    image = Image.alpha_composite(image.convert("RGBA"), overlay)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(output_path, "PNG", quality=95)
    return output_path


class FontSet:
    def __init__(self) -> None:
        self.path = _font_path()
        self.title = _font(self.path, 54)
        self.subtitle = _font(self.path, 25)
        self.h1 = _font(self.path, 30)
        self.h2 = _font(self.path, 24)
        self.body_bold = _font(self.path, 22)
        self.body = _font(self.path, 20)
        self.small = _font(self.path, 17)
        self.tiny = _font(self.path, 14)
        self.hanja = _font(self.path, 52)
        self.icon = _font(self.path, 34)


def _draw_profile(
    layer: Image.Image,
    draw: ImageDraw.ImageDraw,
    plan: dict[str, Any],
    box: tuple[int, int, int, int],
    fonts: FontSet,
    palette: dict[str, str],
    avatar_path: Path | None,
) -> None:
    x0, y0, x1, y1 = box
    _panel(draw, box, radius=22, fill=_hex(palette["paper"], 230), outline=_hex("#DDD0BC"))
    _text(draw, (x0 + 26, y0 + 26), str(plan.get("title", "나의 사주 보고서")), fonts.title, _hex(palette["ink"]), x1 - x0 - 52, 66)
    _text(draw, (x0 + 28, y0 + 94), str(plan.get("subtitle", "내가 가진 기질과 오늘/올해의 흐름")), fonts.subtitle, _hex(palette["ink"]), x1 - x0 - 56, 32, align="center")
    _sparkles(draw, x0 + 30, y0 + 118, palette)

    avatar_box = (x0 + 82, y0 + 155, x1 - 82, y0 + 455)
    avatar = _avatar(avatar_path, (avatar_box[2] - avatar_box[0], avatar_box[3] - avatar_box[1]), palette)
    layer.alpha_composite(avatar, (avatar_box[0], avatar_box[1]))

    profile = plan.get("profile") or {}
    _panel(draw, (x0 + 24, y1 - 118, x1 - 24, y1 - 28), radius=12, fill=_hex("#F4EADB", 240), outline=_hex("#D8C9B5"))
    _badge(draw, (x0 + 172, y1 - 112, x1 - 172, y1 - 82), "한 줄 요약", fonts.small, palette)
    _text(draw, (x0 + 48, y1 - 73), str(profile.get("badge", "내 속도와 기준으로 운을 여는 타입")), fonts.body_bold, _hex(palette["ink"]), x1 - x0 - 96, 44, align="center")


def _draw_saju_grid(
    draw: ImageDraw.ImageDraw,
    plan: dict[str, Any],
    box: tuple[int, int, int, int],
    fonts: FontSet,
    palette: dict[str, str],
) -> None:
    x0, y0, x1, y1 = box
    _section_title(draw, (x0, y0), "1. 사주 구성", fonts, palette)
    card = (x0, y0 + 60, x1, y1 - 28)
    _panel(draw, card, radius=12, fill=_hex(palette["paper"], 232), outline=_hex("#CFC1AD"))

    rows = _saju_grid(plan)
    label_w = 92
    col_w = (card[2] - card[0] - label_w) // 4
    header_h = 62
    row_h = 132
    y = card[1]
    for i, row in enumerate(rows):
        cx = card[0] + label_w + i * col_w
        _line(draw, (cx, y, cx, card[3]), "#D8CCBA")
        _text(draw, (cx, y + 18), row["label"], fonts.body_bold, _hex(palette["ink"]), col_w, 28, align="center")
    _line(draw, (card[0], y + header_h, card[2], y + header_h), "#D8CCBA")
    _line(draw, (card[0], y + header_h + row_h, card[2], y + header_h + row_h), "#D8CCBA")
    _text(draw, (card[0], y + header_h + 45), "위", fonts.body_bold, _hex(palette["ink"]), label_w, 32, align="center")
    _text(draw, (card[0], y + header_h + row_h + 45), "아래", fonts.body_bold, _hex(palette["ink"]), label_w, 32, align="center")

    for i, row in enumerate(rows):
        cx = card[0] + label_w + i * col_w
        color_top = _hex(ELEMENT_COLORS.get(row["top_element"], palette["accent"]))
        color_bottom = _hex(ELEMENT_COLORS.get(row["bottom_element"], palette["accent"]))
        _text(draw, (cx, y + header_h + 28), row["top"], fonts.hanja, color_top, col_w, 60, align="center")
        _text(draw, (cx, y + header_h + 88), f"({row['top_element']})", fonts.small, color_top, col_w, 22, align="center")
        _text(draw, (cx, y + header_h + row_h + 28), row["bottom"], fonts.hanja, color_bottom, col_w, 60, align="center")
        _text(draw, (cx, y + header_h + row_h + 88), f"({row['bottom_element']})", fonts.small, color_bottom, col_w, 22, align="center")

    _panel(draw, (card[0] + 40, card[3] - 70, card[2] - 40, card[3] - 20), radius=10, fill=_hex("#F2E6D5", 240))
    _text(draw, (card[0] + 58, card[3] - 56), str(plan.get("day_master", "성향 키워드: 기준, 실행, 균형")), fonts.body_bold, _hex(palette["ink"]), card[2] - card[0] - 116, 30, align="center")


def _draw_personality(
    draw: ImageDraw.ImageDraw,
    plan: dict[str, Any],
    box: tuple[int, int, int, int],
    fonts: FontSet,
    palette: dict[str, str],
) -> None:
    _section_title(draw, (box[0], box[1]), "2. 나의 성향 분석", fonts, palette)
    items = _list(plan.get("personality"), 4, _default_personality())
    y = box[1] + 70
    for item in items[:4]:
        icon_box = (box[0] + 8, y, box[0] + 72, y + 64)
        draw.ellipse(icon_box, fill=_hex("#E8E0D3"), outline=_hex("#D4C6B5"))
        icon = ICON_LABELS.get(str(item.get("icon", "star")), "★")
        _text(draw, (icon_box[0], icon_box[1] + 15), icon, fonts.icon, _hex(palette["accent"]), 64, 34, align="center")
        _text(draw, (box[0] + 95, y + 2), str(item.get("title", "")), fonts.body_bold, _hex(palette["ink"]), box[2] - box[0] - 110, 28)
        _text(draw, (box[0] + 95, y + 34), str(item.get("body", "")), fonts.body, _hex(palette["ink"]), box[2] - box[0] - 110, 58)
        y += 112


def _draw_elements(
    draw: ImageDraw.ImageDraw,
    plan: dict[str, Any],
    box: tuple[int, int, int, int],
    fonts: FontSet,
    palette: dict[str, str],
) -> None:
    _section_title(draw, (box[0], box[1]), "3. 오행 균형", fonts, palette)
    elements = _elements(plan)
    center = ((box[0] + box[2]) // 2, box[1] + 210)
    radius = 150
    total = sum(max(1, int(e["score"])) for e in elements)
    start = -90
    for e in elements:
        value = max(1, int(e["score"]))
        extent = 360 * value / total
        color = _hex(ELEMENT_COLORS.get(e["name"], "#D8B978"))
        draw.pieslice((center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius), start, start + extent, fill=color, outline=_hex("#FFF9EF"), width=5)
        mid = math.radians(start + extent / 2)
        lx = center[0] + int(math.cos(mid) * 98)
        ly = center[1] + int(math.sin(mid) * 98)
        _text(draw, (lx - 42, ly - 14), f"{e['name']} {e['score']}", fonts.small, _hex(palette["ink"]), 84, 24, align="center")
        start += extent
    draw.ellipse((center[0] - 64, center[1] - 64, center[0] + 64, center[1] + 64), fill=_hex("#FFF9EF"), outline=_hex("#DACCB8"))
    _text(draw, (center[0] - 55, center[1] - 26), "오행\n분포", fonts.body_bold, _hex(palette["ink"]), 110, 60, align="center")

    _panel(draw, (box[0] + 12, box[3] - 112, box[2] - 12, box[3] - 62), radius=12, fill=_hex("#F2E6D5", 240))
    _text(draw, (box[0] + 28, box[3] - 101), str(plan.get("element_summary", "균형을 맞출수록 흐름이 좋아져요.")), fonts.small, _hex(palette["ink"]), box[2] - box[0] - 56, 30, align="center")
    _panel(draw, (box[0] + 12, box[3] - 52, box[2] - 12, box[3] - 2), radius=12, fill=_hex("#F6EDE0", 240))
    _text(draw, (box[0] + 28, box[3] - 42), str(plan.get("element_tip", "부족한 기운은 루틴과 관계 속에서 채워보세요.")), fonts.small, _hex(palette["ink"]), box[2] - box[0] - 56, 30, align="center")


def _draw_fortune_flow(
    draw: ImageDraw.ImageDraw,
    plan: dict[str, Any],
    box: tuple[int, int, int, int],
    fonts: FontSet,
    palette: dict[str, str],
) -> None:
    _section_title(draw, (box[0], box[1]), "4. 오늘 & 올해 흐름", fonts, palette)
    rows = _list(plan.get("fortune_flow"), 4, _default_flow())
    y = box[1] + 68
    for i, row in enumerate(rows[:4]):
        h = 142
        _panel(draw, (box[0] + 8, y, box[2] - 8, y + h), radius=12, fill=_hex("#FFF9EF", 238), outline=_hex("#DACCB8"))
        badge_color = _hex(ELEMENT_COLORS.get(["목", "수", "화", "토"][i], palette["accent"]))
        draw.rounded_rectangle((box[0] + 28, y + 42, box[0] + 70, y + 84), radius=21, fill=badge_color)
        _text(draw, (box[0] + 28, y + 52), str(i + 1), fonts.small, _hex("#FFF9EF"), 42, 22, align="center")
        _text(draw, (box[0] + 96, y + 22), f"• {row.get('title', '')}", fonts.h2, _hex(palette["ink"]), box[2] - box[0] - 126, 32)
        _text(draw, (box[0] + 108, y + 62), str(row.get("body", "")), fonts.body, _hex(palette["ink"]), box[2] - box[0] - 136, 58)
        y += h + 22


def _draw_recommendations(
    draw: ImageDraw.ImageDraw,
    plan: dict[str, Any],
    box: tuple[int, int, int, int],
    fonts: FontSet,
    palette: dict[str, str],
) -> None:
    _section_title(draw, (box[0], box[1]), "5. 적성 & 추천 방향", fonts, palette)
    rec = plan.get("recommendations") or {}
    rows = [
        ("적성 키워드", rec.get("fit_keywords", "기획력, 실행력, 책임감")),
        ("잘 맞는 분야", rec.get("good_fields", "개발, 사업, 교육, 컨설팅")),
        ("피하면 좋은 환경", rec.get("avoid", "기준 없이 급하게 바뀌는 환경")),
    ]
    y = box[1] + 70
    for label, body in rows:
        _panel(draw, (box[0] + 8, y, box[0] + 150, y + 56), radius=10, fill=_hex("#EDE0CC", 245), outline=_hex("#DACCB8"))
        _text(draw, (box[0] + 20, y + 16), label, fonts.body_bold, _hex(palette["ink"]), 126, 26, align="center")
        _text(draw, (box[0] + 170, y + 10), str(body), fonts.body, _hex(palette["ink"]), box[2] - box[0] - 190, 42)
        y += 82
    _panel(draw, (box[0] + 8, box[3] - 84, box[2] - 8, box[3] - 8), radius=12, fill=_hex("#F4E7D4", 245), outline=_hex("#DACCB8"))
    _badge(draw, (box[0] + 28, box[3] - 62, box[0] + 86, box[3] - 34), "TIP", fonts.small, palette)
    tip = str(rec.get("today_tip", "작은 계획 하나를 바로 실행해보세요."))
    year_tip = str(rec.get("year_tip", "올해는 기준을 세우고 꾸준히 밀어붙이면 좋아요."))
    _text(draw, (box[0] + 108, box[3] - 66), f"{tip} {year_tip}", fonts.body, _hex(palette["ink"]), box[2] - box[0] - 136, 48)


def _draw_relationship(
    draw: ImageDraw.ImageDraw,
    plan: dict[str, Any],
    box: tuple[int, int, int, int],
    fonts: FontSet,
    palette: dict[str, str],
) -> None:
    _section_title(draw, (box[0], box[1]), "6. 관계 & 마음관리", fonts, palette)
    rel = plan.get("relationship") or {}
    items = [
        ("♡", "관계 스타일", rel.get("love_style", "한 번 마음을 주면 오래 챙기는 편이에요.")),
        ("◎", "사람관계 조언", rel.get("people_tip", "혼자 다 짊어지기보다 적절히 나눠도 좋아요.")),
    ]
    y = box[1] + 78
    for icon, title, body in items:
        _text(draw, (box[0] + 16, y + 2), icon, fonts.icon, _hex(palette["accent"]), 48, 40, align="center")
        _text(draw, (box[0] + 82, y), title, fonts.body_bold, _hex(palette["ink"]), box[2] - box[0] - 100, 28)
        _text(draw, (box[0] + 82, y + 38), str(body), fonts.body, _hex(palette["ink"]), box[2] - box[0] - 100, 86)
        y += 150
    _panel(draw, (box[0] + 8, box[3] - 96, box[2] - 8, box[3] - 8), radius=12, fill=_hex("#F4E7D4", 245), outline=_hex("#DACCB8"))
    _text(draw, (box[0] + 28, box[3] - 74), f"“{rel.get('quote', '내 속도를 지키면 관계도 편안해져요.')}”", fonts.body_bold, _hex(palette["accent"]), box[2] - box[0] - 56, 52, align="center")


def _draw_closing(
    draw: ImageDraw.ImageDraw,
    plan: dict[str, Any],
    box: tuple[int, int, int, int],
    fonts: FontSet,
    palette: dict[str, str],
) -> None:
    _section_title(draw, (box[0], box[1]), "7. 총평", fonts, palette)
    closing = plan.get("closing") or {}
    _text(draw, (box[0] + 12, box[1] + 72), str(closing.get("summary", "내 기준을 믿고 꾸준히 쌓을수록 좋은 흐름이 커져요.")), fonts.body_bold, _hex(palette["ink"]), box[2] - box[0] - 24, 130)
    _panel(draw, (box[0] + 8, box[3] - 114, box[2] - 8, box[3] - 8), radius=12, fill=_hex("#F4E7D4", 245), outline=_hex("#DACCB8"))
    _text(draw, (box[0] + 28, box[3] - 96), "행운 아이템", fonts.body_bold, _hex(palette["ink"]), 140, 28)
    colors = list(closing.get("lucky_colors") or ["#111111", "#D8B978", "#4E86B7", "#5FA66B"])[:4]
    x = box[0] + 190
    for color in colors:
        draw.ellipse((x, box[3] - 96, x + 34, box[3] - 62), fill=_hex(str(color)), outline=_hex("#CFC1AD"))
        x += 44
    keywords = ", ".join([str(v) for v in (closing.get("lucky_keywords") or ["신뢰", "성장", "실행", "균형"])][:4])
    _text(draw, (box[0] + 28, box[3] - 54), f"키워드  {keywords}", fonts.body_bold, _hex(palette["ink"]), box[2] - box[0] - 56, 32)


def _draw_footer(
    draw: ImageDraw.ImageDraw,
    plan: dict[str, Any],
    box: tuple[int, int, int, int],
    fonts: FontSet,
    palette: dict[str, str],
) -> None:
    footer = str((plan.get("closing") or {}).get("footer", "오늘의 작은 선택이 내일의 운을 만들어요."))
    _line(draw, (box[0], box[1], box[2], box[1]), "#D7C9B6")
    _text(draw, (box[0], box[1] + 22), f"✦ {footer}", fonts.body_bold, _hex(palette["ink"]), box[2] - box[0], 40, align="center")


def _load_background(background_path: Path | None, size: tuple[int, int], palette: dict[str, str]) -> Image.Image:
    width, height = size
    base = Image.new("RGB", size, _rgb(palette["background"]))
    draw = ImageDraw.Draw(base, "RGBA")
    for y in range(0, height, 18):
        alpha = 10 + int(6 * math.sin(y / 80))
        draw.line((0, y, width, y), fill=(255, 255, 255, alpha))
    if background_path and background_path.exists():
        with Image.open(background_path) as img:
            img = _cover(img.convert("RGB"), size).filter(ImageFilter.GaussianBlur(radius=0.4))
        base = Image.blend(base, img, 0.18)
    return base


def _avatar(path: Path | None, size: tuple[int, int], palette: dict[str, str]) -> Image.Image:
    if path and path.exists():
        with Image.open(path) as img:
            img = _cover(img.convert("RGBA"), size)
    else:
        img = Image.new("RGBA", size, _hex("#EDE0CC", 255))
        d = ImageDraw.Draw(img, "RGBA")
        d.ellipse((40, 30, size[0] - 40, size[1] - 10), fill=_hex("#202020"))
        d.ellipse((90, 120, size[0] - 90, size[1] - 70), fill=_hex("#F1C79A"), outline=_hex("#151515"), width=8)
        d.ellipse((140, 190, 172, 222), fill=_hex("#151515"))
        d.ellipse((size[0] - 172, 190, size[0] - 140, 222), fill=_hex("#151515"))
        d.arc((145, 215, size[0] - 145, 295), 10, 170, fill=_hex("#151515"), width=8)
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0], size[1]), radius=28, fill=255)
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out


def _cover(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    width, height = size
    scale = max(width / img.width, height / img.height)
    resized = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    left = (resized.width - width) // 2
    top = (resized.height - height) // 2
    return resized.crop((left, top, left + width, top + height))


def _panel(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    *,
    radius: int,
    fill: tuple[int, int, int, int],
    outline: tuple[int, int, int, int] | None = None,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=2 if outline else 0)


def _section_title(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, fonts: FontSet, palette: dict[str, str]) -> None:
    x, y = xy
    _text(draw, (x, y), text, fonts.h1, _hex(palette["ink"]), 420, 42)


def _badge(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    font: ImageFont.ImageFont,
    palette: dict[str, str],
) -> None:
    draw.rounded_rectangle(box, radius=(box[3] - box[1]) // 2, fill=_hex(palette["accent"], 235))
    _text(draw, (box[0], box[1] + 6), text, font, _hex("#FFF9EF"), box[2] - box[0], box[3] - box[1] - 6, align="center")


def _sparkles(draw: ImageDraw.ImageDraw, x: int, y: int, palette: dict[str, str]) -> None:
    for dx, dy, r in [(0, 0, 8), (28, 30, 5), (390, -42, 7), (422, -10, 4)]:
        cx, cy = x + dx, y + dy
        color = _hex("#D8B978", 180)
        draw.polygon([(cx, cy - r), (cx + r // 2, cy), (cx, cy + r), (cx - r // 2, cy)], fill=color)


def _line(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], color: str) -> None:
    draw.line(box, fill=_hex(color), width=2)


def _text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int, int],
    max_width: int,
    max_height: int,
    *,
    align: str = "left",
    line_spacing: int = 5,
) -> None:
    x, y = xy
    lines = _wrap(draw, text, font, max_width)
    line_h = int(_measure(draw, "가", font)[1]) + line_spacing
    max_lines = max(1, max_height // max(1, line_h))
    clipped = lines[:max_lines]
    if len(lines) > max_lines and clipped:
        clipped[-1] = _ellipsis(draw, clipped[-1], font, max_width)
    for i, line in enumerate(clipped):
        line_w = _measure(draw, line, font)[0]
        lx = x
        if align == "center":
            lx = x + max(0, (max_width - int(line_w)) // 2)
        elif align == "right":
            lx = x + max(0, max_width - int(line_w))
        draw.text((lx, y + i * line_h), line, font=font, fill=fill)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    text = " ".join(str(text).split())
    if not text:
        return [""]
    words = text.split(" ")
    lines: list[str] = []
    line = ""
    for word in words:
        candidate = word if not line else f"{line} {word}"
        if _measure(draw, candidate, font)[0] <= max_width:
            line = candidate
            continue
        if line:
            lines.append(line)
        if _measure(draw, word, font)[0] <= max_width:
            line = word
        else:
            chars: list[str] = []
            for ch in word:
                candidate = "".join(chars) + ch
                if _measure(draw, candidate, font)[0] > max_width and chars:
                    lines.append("".join(chars))
                    chars = [ch]
                else:
                    chars.append(ch)
            line = "".join(chars)
    if line:
        lines.append(line)
    return lines or [""]


def _ellipsis(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> str:
    suffix = "..."
    while text and _measure(draw, text + suffix, font)[0] > max_width:
        text = text[:-1]
    return text + suffix if text else suffix


def _measure(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[float, float]:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def _font_path() -> str | None:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return path
    return None


def _font(path: str | None, size: int) -> ImageFont.ImageFont:
    if path:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def _palette(plan: dict[str, Any]) -> dict[str, str]:
    design = plan.get("design") or {}
    palette = design.get("palette") or {}
    return {
        "background": str(palette.get("background") or "#F7F0E6"),
        "paper": str(palette.get("paper") or "#FFF9EF"),
        "ink": str(palette.get("ink") or "#151515"),
        "accent": str(palette.get("accent") or "#7B6042"),
        "subtle": str(palette.get("subtle") or "#6E6A62"),
    }


def _saju_grid(plan: dict[str, Any]) -> list[dict[str, str]]:
    rows = list(plan.get("saju_grid") or [])
    if not rows:
        legacy = list(plan.get("saju_table") or [])
        for row in legacy[:4]:
            pillar = str(row.get("pillar", "??"))
            rows.append({
                "label": str(row.get("label", "")),
                "top": pillar[:1] or "?",
                "top_element": "목",
                "bottom": pillar[1:2] or "?",
                "bottom_element": "토",
            })
    defaults = [
        {"label": "시주", "top": "?", "top_element": "수", "bottom": "?", "bottom_element": "수"},
        {"label": "일주(나)", "top": "?", "top_element": "토", "bottom": "?", "bottom_element": "토"},
        {"label": "월주", "top": "?", "top_element": "금", "bottom": "?", "bottom_element": "금"},
        {"label": "년주", "top": "?", "top_element": "목", "bottom": "?", "bottom_element": "목"},
    ]
    normalized: list[dict[str, str]] = []
    for i, default in enumerate(defaults):
        src = rows[i] if i < len(rows) and isinstance(rows[i], dict) else {}
        normalized.append({k: str(src.get(k) or default[k]) for k in default})
    return normalized


def _elements(plan: dict[str, Any]) -> list[dict[str, Any]]:
    rows = list(plan.get("elements") or [])
    names = ["목", "화", "토", "금", "수"]
    by_name = {str(row.get("name")): row for row in rows if isinstance(row, dict)}
    result = []
    for name in names:
        row = by_name.get(name, {"name": name, "score": 2, "label": "균형"})
        result.append({"name": name, "score": _clamp_int(row.get("score", 2), 0, 9), "label": str(row.get("label", ""))})
    return result


def _list(value: Any, count: int, fallback: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = value if isinstance(value, list) else []
    normalized = [row for row in rows if isinstance(row, dict)]
    return (normalized + fallback)[:count]


def _default_personality() -> list[dict[str, str]]:
    return [
        {"icon": "mountain", "title": "꾸준한 실행력", "body": "계획을 세우면 끝까지 밀고 가는 힘이 있어요."},
        {"icon": "target", "title": "빠른 판단", "body": "상황을 읽고 필요한 기회를 잘 잡는 편이에요."},
        {"icon": "crown", "title": "안정적인 리더십", "body": "주변을 정리하고 방향을 잡아주는 장점이 있어요."},
        {"icon": "heart", "title": "속깊은 책임감", "body": "표현은 담백해도 오래 챙기는 타입이에요."},
    ]


def _default_flow() -> list[dict[str, str]]:
    return [
        {"title": "오늘", "body": "작은 일부터 정리하면 마음이 가벼워져요."},
        {"title": "이번 달", "body": "기회보다 기준을 먼저 세우면 선택이 쉬워져요."},
        {"title": "2026년", "body": "쌓아둔 실력이 성과로 보이기 쉬운 해예요."},
        {"title": "앞으로", "body": "꾸준함과 신뢰가 가장 큰 자산이 돼요."},
    ]


def _clamp_int(value: Any, lo: int, hi: int) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        n = lo
    return max(lo, min(hi, n))


def _hex(value: str, alpha: int = 255) -> tuple[int, int, int, int]:
    r, g, b = _rgb(value)
    return r, g, b, alpha


def _rgb(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    if len(value) != 6:
        value = "F7F0E6"
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)
