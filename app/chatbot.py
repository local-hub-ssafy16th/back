import re

from openai import OpenAI
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .config import settings
from .models import Location, Post
from .schemas import ChatMessage

TYPE_KEYWORDS: dict[str, str] = {
    "관광지": "12",
    "관광": "12",
    "문화시설": "14",
    "축제": "15",
    "공연": "15",
    "행사": "15",
    "여행코스": "25",
    "레포츠": "28",
    "액티비티": "28",
    "숙박": "32",
    "호텔": "32",
    "쇼핑": "38",
    "음식점": "39",
    "맛집": "39",
}

SYSTEM_PROMPT = """당신은 '동네방네' 서비스의 서울 지역 정보 챗봇입니다.
한국관광공사 TourAPI 데이터를 기반으로 관광지·문화시설·축제공연행사·여행코스·레포츠·숙박·쇼핑 정보를 안내합니다.

다음 두 가지는 보유하고 있지 않은 정보입니다. 관련 질문을 받으면 추측하지 말고 미보유 사실을 명확히 답하세요:
1. 축제·공연행사의 시작일/종료일(일정) — 목록과 위치는 안내할 수 있지만 날짜 정보는 없습니다.
2. 음식점·맛집 데이터 — 전혀 보유하고 있지 않습니다.

아래 [참고 데이터]에 제시된 장소·게시글 정보만을 근거로 답변하고, 목록에 없는 사실을 지어내지 마세요.
관련 정보가 [참고 데이터]에 없으면 모른다고 답하세요."""


class ChatbotUpstreamError(Exception):
    pass


def extract_sigungu(message: str, sigungu_names: dict[str, str]) -> str | None:
    for code, name in sigungu_names.items():
        if name in message:
            return code
    return None


def extract_content_type(message: str) -> str | None:
    for keyword, content_type_id in TYPE_KEYWORDS.items():
        if keyword in message:
            return content_type_id
    return None


def _keyword_tokens(message: str) -> list[str]:
    return [t for t in re.split(r"[\s,.!?~/·]+", message) if len(t) >= 2]


def search_locations(
    db: Session, message: str, sigungu_names: dict[str, str], limit: int = 5
) -> list[Location]:
    sigungu = extract_sigungu(message, sigungu_names)
    content_type = extract_content_type(message)

    query = db.query(Location)
    if sigungu:
        query = query.filter(Location.l_dong_signgu_cd == sigungu)
    if content_type:
        query = query.filter(Location.content_type_id == content_type)

    if not sigungu and not content_type:
        tokens = _keyword_tokens(message)
        if not tokens:
            return []
        query = query.filter(or_(*[Location.title.ilike(f"%{t}%") for t in tokens]))

    return query.limit(limit).all()


def search_posts(db: Session, message: str, limit: int = 3) -> list[Post]:
    tokens = _keyword_tokens(message)
    if not tokens:
        return []
    clauses = []
    for t in tokens:
        clauses.append(Post.title.ilike(f"%{t}%"))
        clauses.append(Post.content.ilike(f"%{t}%"))
    return db.query(Post).filter(or_(*clauses)).order_by(Post.created_at.desc()).limit(limit).all()


def _build_context_text(locations: list[Location], posts: list[Post]) -> str:
    lines: list[str] = []
    if locations:
        lines.append("[지역 정보]")
        for loc in locations:
            lines.append(f"- ({loc.content_type_id}) {loc.title} | {loc.addr1 or '주소 정보 없음'}")
    if posts:
        lines.append("[커뮤니티 게시글]")
        for post in posts:
            lines.append(f"- [{post.category}] {post.title}")
    if not lines:
        lines.append("[참고 데이터 없음]")
    return "\n".join(lines)


def ask_chatbot(
    message: str,
    history: list[ChatMessage],
    locations: list[Location],
    posts: list[Post],
) -> str:
    context_text = _build_context_text(locations, posts)
    messages = [{"role": "system", "content": f"{SYSTEM_PROMPT}\n\n[참고 데이터]\n{context_text}"}]
    for turn in history[-10:]:
        messages.append({"role": turn.role, "content": turn.content})
    messages.append({"role": "user", "content": message})

    client = OpenAI(api_key=settings.openai_api_key)
    try:
        completion = client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            timeout=30.0,
        )
    except Exception as exc:
        raise ChatbotUpstreamError(str(exc)) from exc

    reply = completion.choices[0].message.content
    if not reply:
        raise ChatbotUpstreamError("빈 응답을 받았습니다.")
    return reply
