"""Pillow renderer for the final Korean saju info card."""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageFilter

WIDTH = 1080
HEIGHT = 1920

FONT_CANDIDATES = [
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
    "/System/Library/Fonts/Supplemental/NotoSansCJK-Regular.ttc",
    "/Library/Fonts/NanumGothic.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
]

ELEMENT_COLORS = {
    "목": "#3E8B63",
    "화": "#E85D4F",
    "토": "#B88942",
    "금": "#7D8792",
    "수": "#4068B0",
}


def render_card(
    plan: dict[str, Any],
    output_path: Path,
    *,
    background_path: Path | None = None,
    size: tuple[int, int] = (WIDTH, HEIGHT),
) -> Path:
    width, height = size
    palette = _palette(plan)
    image = _load_background(background_path, size, palette)
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    fonts = FontSet()
    margin = 54
    paper = _hex(palette["paper"], alpha=236)
    ink = _hex(palette["ink"])
    subtle = _hex(palette["subtle"])
    accent = _hex(palette["accent"])

    _panel(draw, (margin, 48, width - margin, 245), radius=34, fill=paper)
    _text(draw, (margin + 34, 78), str(plan.get("title", "대만신 사주 카드")), fonts.title, ink, width - 2 * margin - 68, 62)
    _text(draw, (margin + 36, 148), str(plan.get("subtitle", "타고난 결을 한 장에 정리했단다.")), fonts.body_bold, accent, width - 2 * margin - 72, 34)
    _text(draw, (margin + 36, 190), str(plan.get("birth_line", "")), fonts.small, subtle, width - 2 * margin - 72, 42)

    y = 270
    _draw_saju_table(draw, plan, (margin, y, width - margin, y + 205), fonts, palette)
    y += 230
    _draw_elements(draw, plan, (margin, y, width - margin, y + 230), fonts, palette)
    y += 255
    _draw_thirteen_points(draw, plan, (margin, y, width - margin, y + 640), fonts, palette)
    y += 665
    _draw_questions(draw, plan, (margin, y, width - margin, y + 210), fonts, palette)
    y += 235
    _draw_advice(draw, plan, (margin, y, width - margin, height - 82), fonts, palette)

    image = Image.alpha_composite(image.convert("RGBA"), overlay)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(output_path, "PNG", quality=95)
    return output_path


class FontSet:
    def __init__(self) -> None:
        self.path = _font_path()
        self.title = _font(self.path, 50)
        self.h1 = _font(self.path, 31)
        self.h2 = _font(self.path, 25)
        self.body_bold = _font(self.path, 28)
        self.body = _font(self.path, 24)
        self.small = _font(self.path, 20)
        self.tiny = _font(self.path, 17)


def _draw_saju_table(
    draw: ImageDraw.ImageDraw,
    plan: dict[str, Any],
    box: tuple[int, int, int, int],
    fonts: FontSet,
    palette: dict[str, str],
) -> None:
    x0, y0, x1, y1 = box
    _panel(draw, box, radius=26, fill=_hex(palette["paper"], alpha=238))
    _section_title(draw, (x0 + 28, y0 + 22), "명식 한눈에", fonts, palette)
    note = str(plan.get("reading_note", "간이 명식은 정밀 감정과 다를 수 있단다."))
    _text(draw, (x0 + 212, y0 + 27), note, fonts.tiny, _hex(palette["subtle"]), x1 - x0 - 240, 28)

    cells = _saju_table(plan)
    gap = 14
    cell_w = (x1 - x0 - 56 - gap * 3) // 4
    y = y0 + 76
    for i, cell in enumerate(cells[:4]):
        cx = x0 + 28 + i * (cell_w + gap)
        _panel(draw, (cx, y, cx + cell_w, y1 - 24), radius=20, fill=(255, 255, 255, 210), outline=_hex("#E5DED0", alpha=220))
        _text(draw, (cx + 16, y + 16), str(cell.get("label", "")), fonts.tiny, _hex(palette["subtle"]), cell_w - 32, 24, align="center")
        _text(draw, (cx + 12, y + 45), str(cell.get("pillar", "미상")), fonts.h1, _hex(palette["ink"]), cell_w - 24, 44, align="center")
        _text(draw, (cx + 14, y + 96), str(cell.get("meaning", "")), fonts.tiny, _hex(palette["ink"]), cell_w - 28, 48, align="center")


def _draw_elements(
    draw: ImageDraw.ImageDraw,
    plan: dict[str, Any],
    box: tuple[int, int, int, int],
    fonts: FontSet,
    palette: dict[str, str],
) -> None:
    x0, y0, x1, y1 = box
    _panel(draw, box, radius=26, fill=_hex(palette["paper"], alpha=238))
    _section_title(draw, (x0 + 28, y0 + 22), "오행 밸런스", fonts, palette)
    keywords = [str(v) for v in plan.get("core_keywords", [])][:3]
    chip_x = x1 - 28
    for keyword in reversed(keywords):
        w = int(_measure(draw, keyword, fonts.small)[0]) + 34
        chip_x -= w
        _pill(draw, (chip_x, y0 + 20, chip_x + w, y0 + 56), keyword, fonts.tiny, palette)
        chip_x -= 10

    elements = _elements(plan)
    y = y0 + 76
    row_h = 29
    max_bar_w = x1 - x0 - 235
    for idx, item in enumerate(elements[:5]):
        name = str(item.get("name", "?"))
        score = _clamp_int(item.get("score", 0), 0, 100)
        summary = str(item.get("summary", ""))
        cy = y + idx * row_h
        color = _hex(ELEMENT_COLORS.get(name, palette["accent"]))
        _text(draw, (x0 + 30, cy - 2), name, fonts.small, color, 38, row_h)
        draw.rounded_rectangle((x0 + 76, cy + 5, x0 + 76 + max_bar_w, cy + 19), radius=8, fill=_hex("#EDE6D8", alpha=230))
        draw.rounded_rectangle((x0 + 76, cy + 5, x0 + 76 + int(max_bar_w * score / 100), cy + 19), radius=8, fill=color)
        _text(draw, (x0 + 92 + max_bar_w, cy - 3), f"{score}", fonts.tiny, _hex(palette["ink"]), 44, row_h)
        _text(draw, (x0 + 143 + max_bar_w, cy - 3), summary, fonts.tiny, _hex(palette["subtle"]), x1 - (x0 + 143 + max_bar_w) - 28, row_h)


def _draw_thirteen_points(
    draw: ImageDraw.ImageDraw,
    plan: dict[str, Any],
    box: tuple[int, int, int, int],
    fonts: FontSet,
    palette: dict[str, str],
) -> None:
    x0, y0, x1, y1 = box
    _panel(draw, box, radius=26, fill=_hex(palette["paper"], alpha=238))
    _section_title(draw, (x0 + 28, y0 + 22), "프리미엄 13단계 요약", fonts, palette)

    points = _thirteen_points(plan)
    col_gap = 18
    row_gap = 9
    col_w = (x1 - x0 - 56 - col_gap) // 2
    row_h = 62
    start_y = y0 + 78
    for i, point in enumerate(points[:13]):
        col = i % 2
        row = i // 2
        px = x0 + 28 + col * (col_w + col_gap)
        py = start_y + row * (row_h + row_gap)
        if py + row_h > y1 - 22:
            break
        _panel(draw, (px, py, px + col_w, py + row_h), radius=18, fill=(255, 255, 255, 205), outline=_hex("#E5DED0", alpha=210))
        num = int(point.get("number", i + 1))
        draw.ellipse((px + 14, py + 16, px + 48, py + 50), fill=_hex(palette["accent"], alpha=235))
        _text(draw, (px + 14, py + 20), str(num), fonts.tiny, (255, 255, 255, 255), 34, 22, align="center")
        _text(draw, (px + 60, py + 7), str(point.get("title", "")), fonts.small, _hex(palette["ink"]), col_w - 76, 24)
        _text(draw, (px + 60, py + 33), str(point.get("summary", "")), fonts.tiny, _hex(palette["subtle"]), col_w - 76, 24)


def _draw_questions(
    draw: ImageDraw.ImageDraw,
    plan: dict[str, Any],
    box: tuple[int, int, int, int],
    fonts: FontSet,
    palette: dict[str, str],
) -> None:
    x0, y0, x1, y1 = box
    _panel(draw, box, radius=26, fill=_hex(palette["paper"], alpha=238))
    _section_title(draw, (x0 + 28, y0 + 20), "질문에 대한 만신의 답", fonts, palette)
    answers = list(plan.get("question_answers") or [])[:3]
    if not answers:
        _text(draw, (x0 + 30, y0 + 78), "지금은 큰 질문보다 내 결을 정돈하는 시간이란다. 조급함을 덜고 한 걸음씩 보거라.", fonts.body, _hex(palette["ink"]), x1 - x0 - 60, 88)
        return
    y = y0 + 70
    for answer in answers:
        q = str(answer.get("question", "")).strip()
        a = str(answer.get("answer", "")).strip()
        _text(draw, (x0 + 30, y), f"Q. {q}", fonts.tiny, _hex(palette["accent"]), x1 - x0 - 60, 24)
        _text(draw, (x0 + 30, y + 26), f"A. {a}", fonts.small, _hex(palette["ink"]), x1 - x0 - 60, 34)
        y += 58
        if y > y1 - 42:
            break


def _draw_advice(
    draw: ImageDraw.ImageDraw,
    plan: dict[str, Any],
    box: tuple[int, int, int, int],
    fonts: FontSet,
    palette: dict[str, str],
) -> None:
    x0, y0, x1, y1 = box
    _panel(draw, box, radius=30, fill=_hex("#111923", alpha=224), outline=_hex(palette["accent"], alpha=180))
    _text(draw, (x0 + 32, y0 + 26), "대만신의 한마디", fonts.h2, _hex(palette["paper"]), x1 - x0 - 64, 36)
    advice = str(plan.get("manse_advice", "네 사주는 결국 네가 어떻게 쓰느냐에 따라 빛이 달라진단다."))
    _text(draw, (x0 + 32, y0 + 72), advice, fonts.body_bold, _hex("#FFF8EC"), x1 - x0 - 64, 86)
    caution = str(plan.get("caution", "사주는 자기성찰용이며 중요한 결정은 현실 정보와 전문가 조언을 함께 보거라."))
    _text(draw, (x0 + 32, y1 - 48), caution, fonts.tiny, _hex("#C7CED8"), x1 - x0 - 64, 30)


def _load_background(background_path: Path | None, size: tuple[int, int], palette: dict[str, str]) -> Image.Image:
    if background_path and background_path.exists():
        with Image.open(background_path) as img:
            img = img.convert("RGB")
            return _cover(img, size).filter(ImageFilter.GaussianBlur(radius=0.2))
    width, height = size
    top = _rgb(palette["background"])
    bottom = _rgb("#243244")
    img = Image.new("RGB", size)
    px = img.load()
    for y in range(height):
        t = y / max(1, height - 1)
        wave = 0.04 * math.sin(t * math.pi * 4)
        for x in range(width):
            v = min(1.0, max(0.0, t + wave))
            px[x, y] = tuple(int(top[i] * (1 - v) + bottom[i] * v) for i in range(3))
    return img


def _cover(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    width, height = size
    scale = max(width / img.width, height / img.height)
    new_size = (int(img.width * scale), int(img.height * scale))
    img = img.resize(new_size, Image.LANCZOS)
    left = (img.width - width) // 2
    top = (img.height - height) // 2
    return img.crop((left, top, left + width, top + height))


def _panel(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    *,
    radius: int,
    fill: tuple[int, int, int, int],
    outline: tuple[int, int, int, int] | None = None,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=1 if outline else 0)


def _pill(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    font: ImageFont.ImageFont,
    palette: dict[str, str],
) -> None:
    draw.rounded_rectangle(box, radius=18, fill=_hex(palette["accent"], alpha=220))
    _text(draw, (box[0], box[1] + 7), text, font, (255, 255, 255, 255), box[2] - box[0], 20, align="center")


def _section_title(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, fonts: FontSet, palette: dict[str, str]) -> None:
    x, y = xy
    draw.rounded_rectangle((x, y + 4, x + 8, y + 34), radius=4, fill=_hex(palette["accent"]))
    _text(draw, (x + 18, y), text, fonts.h2, _hex(palette["ink"]), 360, 38)


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
            chars = []
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
        "background": str(palette.get("background") or "#101820"),
        "paper": str(palette.get("paper") or "#FFF8EC"),
        "ink": str(palette.get("ink") or "#1B1B1F"),
        "accent": str(palette.get("accent") or "#FF6B57"),
        "subtle": str(palette.get("subtle") or "#6F7D8C"),
    }


def _saju_table(plan: dict[str, Any]) -> list[dict[str, Any]]:
    rows = list(plan.get("saju_table") or [])
    labels = ["년주", "월주", "일주", "시주"]
    while len(rows) < 4:
        rows.append({"label": labels[len(rows)], "pillar": "미상", "meaning": "정보 필요"})
    return rows


def _elements(plan: dict[str, Any]) -> list[dict[str, Any]]:
    rows = list(plan.get("elements") or [])
    names = ["목", "화", "토", "금", "수"]
    by_name = {str(row.get("name")): row for row in rows}
    return [by_name.get(name, {"name": name, "score": 20, "summary": "균형 확인"}) for name in names]


def _thirteen_points(plan: dict[str, Any]) -> list[dict[str, Any]]:
    rows = list(plan.get("thirteen_points") or [])
    titles = [
        "전체 그릇", "음양오행", "십성 흐름", "십이운성", "살과 귀인", "연애/결혼", "재물운",
        "직업운", "건강운", "대운", "2026-2035", "질문 답변", "인생상담",
    ]
    while len(rows) < 13:
        i = len(rows)
        rows.append({"number": i + 1, "title": titles[i], "summary": "차분히 열리는 운"})
    return rows


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
        value = "101820"
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)
