"""Prompts for structured saju card planning."""
from __future__ import annotations

import re
from typing import Any


MODEL = "gpt-5.5"
DEFAULT_SIZE = (1472, 1856)


SAJU_PLAN_SYSTEM_PROMPT = """
너는 세계 최고 수준의 사주 리더이자 한국어 운세 리포트 작가다.
사용자의 생년월일과 이미 계산된 사주 명식(bazi)을 바탕으로, 누구나 재미있게
읽을 수 있는 1장짜리 "나의 사주 보고서" 이미지에 들어갈 JSON을 만든다.

참조 방향:
- 점신/포스텔러/SAJU류 앱처럼 오늘의 흐름, 올해의 방향, 한 줄 요약, 실천 팁을 앞에 둔다.
- 어려운 명리 용어를 길게 설명하지 않는다. 최종 문장은 쉬운 말로 바꾼다.
- MZ, 주부, 직장인, 학생 모두 이해할 수 있게 생활 언어로 쓴다.
- 무속인/만신/아저씨 말투, 반말, 겁주는 표현, 저주/불행 예언을 쓰지 않는다.
- "AI", "GPT", "모델", "API", "생성", "정밀 보정", "제공 정보 기반" 같은 기술/제작 메모를 절대 쓰지 않는다.
- 말투는 밝고 다정한 운세 앱 톤: "~해요", "~좋아요", "~추천해요".
- 의료, 법률, 투자, 생명 안전 판단은 단정하지 말고 생활 팁 수준으로 쓴다.
- 한 줄은 짧게. 카드 안에 들어가므로 문장은 밀도 있게 쓴다.
- bazi.status가 ok이면 사주 구성, 오행, 일간 해석은 반드시 bazi.pillars와 bazi.day_master를 기준으로 한다.
- bazi.interpretation_seeds를 참고하되 그대로 복사하지 말고 자연스러운 운세 풀이로 확장한다.
- 사용자의 관심사(개발, 사업, 계약, 가족 등)가 있으면 직업/돈/관계 문장에 자연스럽게 반영한다.
- "오늘"은 작은 실행 팁, "2026년"은 올해의 큰 방향과 조심할 포인트를 함께 쓴다.
- 내용은 진짜 사주를 보는 리포트처럼 명식 근거가 보여야 한다. 다만 최종 표현은 "단단한 금속 같은 기준", "차가운 계절의 신중함"처럼 쉬운 결론 중심으로 쓴다.
- 최종 카드에 한자 명식표가 꼭 들어갈 필요는 없다. 해석은 실제 명식에 기반하되 사용자가 바로 이해하는 한국어를 우선한다.

반드시 raw JSON object만 반환한다. 마크다운, 코드펜스, 설명 문장은 금지다.

JSON schema:
{
  "title": "나의 사주 보고서",
  "subtitle": "내가 가진 기질과 오늘/올해의 흐름",
  "birth_line": "사용자 생년월일 요약",
  "profile": {
    "badge": "한 줄 요약 26자 이내",
    "archetype": "예: 전략형 리더"
  },
  "saju_grid": [
    {"label": "시주", "top": "壬", "top_element": "수", "bottom": "子", "bottom_element": "수"},
    {"label": "일주(나)", "top": "戊", "top_element": "토", "bottom": "辰", "bottom_element": "토"},
    {"label": "월주", "top": "辛", "top_element": "금", "bottom": "酉", "bottom_element": "금"},
    {"label": "년주", "top": "乙", "top_element": "목", "bottom": "卯", "bottom_element": "목"}
  ],
  "day_master": "일간(나): 무토 | 성향 키워드: 현실적, 책임감, 중심 잡는 사람",
  "personality": [
    {"icon": "mountain", "title": "현실적인 실행가", "body": "명식 근거를 반영한 성향 풀이 55자 이내"},
    {"icon": "target", "title": "빠른 판단", "body": "명식 근거를 반영한 성향 풀이 55자 이내"},
    {"icon": "crown", "title": "안정적인 리더십", "body": "명식 근거를 반영한 성향 풀이 55자 이내"},
    {"icon": "heart", "title": "속깊은 정", "body": "명식 근거를 반영한 성향 풀이 55자 이내"}
  ],
  "elements": [
    {"name": "목", "score": 2, "label": "성장"},
    {"name": "화", "score": 1, "label": "표현"},
    {"name": "토", "score": 3, "label": "중심"},
    {"name": "금", "score": 2, "label": "판단"},
    {"name": "수", "score": 2, "label": "지혜"}
  ],
  "element_summary": "오행을 쉬운 말로 요약한 45자 이내 문장",
  "element_tip": "부족한 부분을 보완하는 생활 팁 55자 이내",
  "fortune_flow": [
    {"title": "오늘", "body": "오늘의 흐름과 행동 팁 46자 이내"},
    {"title": "이번 달", "body": "이번 달 주의점과 기회 46자 이내"},
    {"title": "2026년", "body": "올해의 큰 방향 46자 이내"},
    {"title": "앞으로", "body": "길게 가져갈 태도 46자 이내"}
  ],
  "recommendations": {
    "fit_keywords": "기획력, 실행력, 분석력",
    "good_fields": "개발, 사업, 교육, 컨설팅",
    "avoid": "즉흥적이고 기준 없는 환경",
    "today_tip": "오늘 바로 해볼 작은 행동 28자 이내",
    "year_tip": "올해 기억할 전략 28자 이내"
  },
  "relationship": {
    "love_style": "연애/가족/동료 관계에서 보이는 스타일",
    "people_tip": "사람관계 팁",
    "quote": "짧은 응원 문장"
  },
  "closing": {
    "summary": "총평 90자 이내",
    "lucky_colors": ["#111111", "#D8B978", "#4E86B7", "#5FA66B"],
    "lucky_keywords": ["신뢰", "성장", "실행", "균형"],
    "footer": "가볍고 따뜻한 마무리 문장"
  }
}

saju_grid의 한자는 확신이 부족하면 "?"로 둬도 된다. 대신 해석 문장은 자신 있게 생활 언어로 쓴다.
fortune_flow에는 사용자가 묻지 않아도 오늘과 올해 흐름을 반드시 포함한다.
각 해석에는 "왜 그런지"가 보이도록 오행/일간/월지 중 하나의 근거를 쉬운 말로 녹인다.
Return JSON only.
""".strip()


FINAL_CARD_IMAGE_INSTRUCTIONS = """
너는 한국어 타이포그래피와 정보형 포토카드 디자인에 강한 최상급 프로덕션 디자이너다.
사용자의 사주 리포트 내용을 바탕으로 세로형 이미지 1장을 완성한다.

절대 조건:
- 최종 이미지는 한 장의 완성된 사주 포토 카드여야 한다.
- 프로필 이미지는 카드 안에 함께 포함한다. 별도 이미지처럼 분리하지 않는다.
- 카드 안의 모든 한국어 텍스트는 프롬프트의 문구를 최대한 정확하고 선명하게 렌더링한다.
- 한자 명식표는 만들지 않는다. 사주 근거는 쉬운 한국어 문장으로만 보여준다.
- 기술 메모, 모델명, API, 제작 과정, "프롬프트"라는 단어는 이미지에 넣지 않는다.
- 기존 예시 이미지를 베끼지 말고 새 레이아웃으로 디자인한다.
- 공포스럽거나 무속인 같은 톤, 부적/귀신/점집 분위기, 과한 예언 문구는 피한다.
- 작은 상황 만화 일러스트를 3~4개 넣는다. 개발, 계약, 가족, 오늘의 실행 팁을 쉽고 재미있게 이해시키는 귀여운 컷이어야 한다.
""".strip()


def build_final_card_prompt(
    plan: dict[str, Any],
    user_info: dict[str, Any],
    *,
    size: tuple[int, int] = DEFAULT_SIZE,
) -> str:
    """Build one long prompt that asks the image model for the finished card."""

    name = _clean(user_info.get("name"), "나")
    report_date = _clean(user_info.get("report_date"), "오늘")
    birth_line = _clean(plan.get("birth_line"), _clean(user_info.get("birth"), "생년월일"))
    profile = plan.get("profile") if isinstance(plan.get("profile"), dict) else {}
    closing = plan.get("closing") if isinstance(plan.get("closing"), dict) else {}
    recommendations = plan.get("recommendations") if isinstance(plan.get("recommendations"), dict) else {}
    relationship = plan.get("relationship") if isinstance(plan.get("relationship"), dict) else {}
    bazi = user_info.get("bazi") if isinstance(user_info.get("bazi"), dict) else {}
    day_master = bazi.get("day_master") if isinstance(bazi.get("day_master"), dict) else {}

    raw_title = _clean(plan.get("title"), "")
    title = f"{name}님의 사주 포토 카드" if raw_title in {"", "나의 사주 보고서", "사주 보고서"} else raw_title
    subtitle = _clean(plan.get("subtitle"), "내 기질과 오늘/올해의 흐름")
    badge = _clean(profile.get("badge"), "기준을 세우고 기회를 만드는 타입")
    archetype = _clean(profile.get("archetype"), "전략형 실행가")
    plain_basis = _plain_basis_text(bazi)
    personality = _bullets(plan.get("personality"), 4)
    elements = _elements_text(plan)
    flow = _flow_text(plan)
    interests = ", ".join(user_info.get("interests") or []) or "일, 관계, 성장"
    questions = "; ".join(user_info.get("questions") or []) or "추가 질문 없음"
    profile_visual = _profile_visual(str(day_master.get("gan") or ""), interests)

    return f"""
세로 {size[0]}x{size[1]} 한 장짜리 완성 이미지. 실제 손에 들 수 있는 상급 실물 사주 포토카드를 정면에서 촬영한 느낌으로 만든다. 선명한 인쇄 품질, 두꺼운 라미네이팅 카드, 유리 코팅 광택, 은은한 홀로그램 박, 작은 별빛 반사, 가장자리 하이라이트, 미세한 펄 입자와 부드러운 그림자를 넣는다. 배경은 따뜻한 아이보리와 차콜, 실버, 딥그린, 포인트 골드가 섞인 고급 팔레트. 과한 무속 느낌 없이 세련된 운세 앱 + 프리미엄 포토카드 무드.

레이아웃은 기존 참고 이미지와 다르게 리디자인한다. 상단에는 큰 타이틀과 한 줄 요약, 중앙에는 프로필 일러스트와 핵심 해석, 하단에는 오늘/2026년/일과 계약/가족 조언을 촘촘하지만 깔끔한 정보 블록으로 배치한다. 한자 명식표, 팔자 표, 천간/지지 표는 넣지 않는다. 텍스트가 더 많아 보이되 줄간격을 넉넉히 두고, 모든 한글은 또렷하게 읽힌다.

프로필 이미지는 카드 안에 직접 포함한다. {profile_visual} 실존 인물이나 유명 캐릭터를 닮지 않게, 고급 매거진 삽화처럼 그린다. NFT 원숭이, 장난감 마스코트, 점집 할아버지, 만신 캐릭터는 금지.

카드 곳곳에 작은 만화 컷 4개를 넣는다. 노트북 앞에서 구조를 짜는 개발자 컷, 계약서를 체크하는 손과 체크 표시 컷, 가족 식탁에서 대화하는 따뜻한 컷, 오늘 할 일을 정리하는 작은 캘린더 컷. 만화 컷은 귀엽고 이해를 돕는 보조 요소이며, 전체는 고급 포토카드 품질을 유지한다.

카드에 들어갈 텍스트는 아래 문구를 그대로 사용한다.
타이틀: {title}
서브타이틀: {subtitle}
기준일: {report_date} 오늘의 흐름
생년월일: {birth_line}
한 줄 요약: {badge}
타입: {archetype}

1. 나의 기본 기질
{plain_basis}

2. 핵심 성향
{personality}

3. 오행 밸런스
{elements}
해석: {_clean(plan.get("element_summary"), "판단과 지속력이 받쳐주고 표현은 의식적으로 키우면 좋아요.")}
보완: {_clean(plan.get("element_tip"), "따뜻한 대화와 꾸준한 공유가 운의 통로를 넓혀줘요.")}

4. 오늘과 올해
{flow}

5. 일 · 사업 · 계약
관심사: {interests}
잘 맞는 키워드: {_clean(recommendations.get("fit_keywords"), "기획력, 실행력, 분석력")}
잘 맞는 분야: {_clean(recommendations.get("good_fields"), "개발, 사업, 컨설팅, 계약 관리")}
주의할 환경: {_clean(recommendations.get("avoid"), "즉흥적이고 기준 없는 환경")}
오늘 팁: {_clean(recommendations.get("today_tip"), "중요한 약속은 문서로 남기기")}
올해 전략: {_clean(recommendations.get("year_tip"), "확장보다 신뢰 구조 먼저 만들기")}

6. 가족 · 관계
관계 스타일: {_clean(relationship.get("love_style"), "속정은 깊고 표현은 담백한 편이에요.")}
관계 팁: {_clean(relationship.get("people_tip"), "혼자 책임지기보다 역할을 나누면 마음이 가벼워져요.")}
한마디: {_clean(relationship.get("quote"), "기준은 단단하게, 표현은 조금 더 따뜻하게.")}

7. 총평
{_clean(closing.get("summary"), "당신의 운은 빠른 한 방보다 신뢰와 구조를 쌓을 때 크게 열려요. 지금의 선택이 10년 뒤 자산이 됩니다.")}
행운 컬러: 블랙, 실버, 골드, 딥그린
행운 키워드: {", ".join(closing.get("lucky_keywords") or ["신뢰", "성장", "실행", "균형"])}
질문 메모: {questions}
푸터: {_clean(closing.get("footer"), "오늘의 작은 정리가 내일의 큰 운을 만듭니다.")}
""".strip()


def _clean(value: Any, fallback: str = "") -> str:
    text = " ".join(str(value or fallback).split())
    text = re.sub(r"[\u3400-\u9fff]+", "", text)
    return text[:160]


def _bullets(items: Any, limit: int) -> str:
    if not isinstance(items, list):
        items = []
    lines: list[str] = []
    for item in items[:limit]:
        if isinstance(item, dict):
            title = _clean(item.get("title"))
            body = _clean(item.get("body"))
            if title or body:
                lines.append(f"- {title}: {body}")
        else:
            lines.append(f"- {_clean(item)}")
    return "\n".join(lines) or "- 기준이 분명하고 책임감 있게 결과를 만드는 사람\n- 판단이 빠르지만 관계에서는 따뜻한 표현을 더하면 좋아요"


def _flow_text(plan: dict[str, Any]) -> str:
    items = plan.get("fortune_flow")
    if not isinstance(items, list):
        items = []
    lines = []
    for item in items[:4]:
        if isinstance(item, dict):
            lines.append(f"- {_clean(item.get('title'))}: {_clean(item.get('body'))}")
    return "\n".join(lines) or "- 오늘: 정리와 확인이 운을 살려요\n- 2026년: 신뢰를 쌓은 계약과 장기 프로젝트가 좋아요"


def _elements_text(plan: dict[str, Any]) -> str:
    items = plan.get("elements")
    if not isinstance(items, list):
        items = []
    parts = []
    for item in items:
        if isinstance(item, dict):
            parts.append(f"{_clean(item.get('name'))} {item.get('score', 0)}({_clean(item.get('label'))})")
    return " · ".join(parts) or "목 1(성장) · 화 1(표현) · 토 2(중심) · 금 2(판단) · 수 2(지혜)"


def _plain_basis_text(bazi: dict[str, Any]) -> str:
    day = bazi.get("day_master") if isinstance(bazi.get("day_master"), dict) else {}
    gan = str(day.get("gan") or "")
    counts = bazi.get("element_counts") if isinstance(bazi.get("element_counts"), dict) else {}
    strong = ", ".join(str(v) for v in bazi.get("strong_elements") or []) or "균형"
    weak = ", ".join(str(v) for v in bazi.get("weak_elements") or []) or "보완 기운"
    day_phrase = {
        "甲": "큰 나무처럼 방향을 잡고 밀고 가는 사람",
        "乙": "풀과 꽃처럼 유연하게 기회를 키우는 사람",
        "丙": "햇살처럼 분위기를 열고 표현하는 사람",
        "丁": "촛불처럼 집중력과 감각이 깊은 사람",
        "戊": "큰 산처럼 중심을 잡고 버티는 사람",
        "己": "좋은 흙처럼 현실감과 돌봄이 강한 사람",
        "庚": "단단한 금속처럼 기준과 결단이 분명한 사람",
        "辛": "잘 다듬은 보석처럼 완성도와 감각이 있는 사람",
        "壬": "큰 물처럼 생각의 폭과 이동성이 큰 사람",
        "癸": "비와 안개처럼 관찰력과 촉이 섬세한 사람",
    }.get(gan, "자기 기준으로 흐름을 정리하는 사람")
    balance = " · ".join(f"{name} {int(counts.get(name, 0) or 0)}" for name in ["목", "화", "토", "금", "수"])
    return (
        f"- 기본 기질: {day_phrase}\n"
        f"- 강한 흐름: {strong} 기운이 받쳐 판단, 지속력, 정보 감각을 살리기 좋아요\n"
        f"- 보완 포인트: {weak} 쪽은 표현, 확장, 따뜻한 공유로 채우면 운이 부드러워져요\n"
        f"- 균형 메모: {balance}"
    )


def _profile_visual(day_gan: str, interests: str) -> str:
    if day_gan in {"庚", "辛"}:
        return f"금 기운에 맞춘 차분한 실버 톤의 인물형 프로필, 개발·사업·계약 감각이 보이는 노트북과 작은 문서 아이콘, 단단한 눈빛과 세련된 재킷. 관심사: {interests}."
    if day_gan in {"甲", "乙"}:
        return f"목 기운에 맞춘 산뜻한 그린 톤의 인물형 프로필, 성장과 기획을 상징하는 노트와 새싹 빛 장식. 관심사: {interests}."
    if day_gan in {"丙", "丁"}:
        return f"화 기운에 맞춘 따뜻한 코랄 톤의 인물형 프로필, 표현력과 활력을 보여주는 부드러운 빛 장식. 관심사: {interests}."
    if day_gan in {"戊", "己"}:
        return f"토 기운에 맞춘 베이지와 골드 톤의 인물형 프로필, 안정감과 책임감을 보여주는 산과 문서 장식. 관심사: {interests}."
    return f"수 기운에 맞춘 딥블루 톤의 인물형 프로필, 정보 감각과 흐름 읽기를 상징하는 잔물결과 별빛 장식. 관심사: {interests}."
