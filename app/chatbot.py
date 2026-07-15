import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException
from openai import AsyncOpenAI
from .config import settings
from .schemas import ChatMessage, ChatResponse, LocationRef, PostRef
from .services import analyze_message, search_locations, search_posts, CONTENT_TYPE_NAMES, SIGUNGU_NAMES

logger = logging.getLogger(__name__)

# OpenAI 비동기 클라이언트 초기화 (키가 없어도 객체 생성은 허용하되 호출 시 예외 처리)
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY or "dummy_key")

SYSTEM_PROMPT = """당신은 서울(SEL) 권역 공공데이터 기반 지역 정보 공유 커뮤니티인 '동네방네'의 친절하고 전문적인 AI 가이드 챗봇입니다.
사용자에게 서울 지역의 관광지, 문화시설, 축제/행사, 여행코스, 레포츠, 숙박, 쇼핑 정보를 안내합니다.

[⚠️ 중요 제약사항 - 필수 준수]
1. 음식점/맛집 정보 미보유:
   현재 서울 지역의 음식점(맛집, 식당, 카페 등) 데이터는 수집되지 않아 제공이 불가능합니다. 사용자가 맛집이나 식당 추천을 요구할 경우, 반드시 "죄송합니다. 현재 음식점 데이터는 제공되지 않습니다. 대신 서울의 관광지, 문화시설, 축제 정보를 안내해 드릴 수 있습니다."와 같이 사실대로 데이터 미보유 상태를 정중히 답변하십시오. 임의로 맛집을 지어내거나 추천하지 마십시오.
2. 축제 일정(날짜) 정보 미보유:
   현재 축제 및 공연행사(contentTypeId=15) 데이터에는 시작 날짜와 종료 날짜 필드가 존재하지 않습니다. 사용자가 축제의 일정이나 특정 날짜를 문의할 경우, 반드시 "죄송합니다. 현재 축제의 시작 및 종료 날짜 정보는 보유하고 있지 않습니다. 대신 축제의 이름, 위치, 소개 정보는 안내해 드릴 수 있습니다."라고 답변하십시오. 날짜를 임의로 지어내어 답변하면 절대 안 됩니다.
3. 서울 외 지역 정보 미보유:
   본 서비스는 서울(SEL) 권역 데이터만 보유하고 있습니다. 서울 이외의 지역에 대해 묻는 경우 서울 권역 정보만 안내 가능함을 알리십시오.
4. 환각 방지:
   제공된 데이터베이스 검색 결과(Context)에 없는 정보(전화번호, 주소, 상세 특징 등)를 지어내어 답변하지 마십시오. 데이터가 없는 경우 정중히 모른다고 답변하거나, 제공된 정보를 기반으로만 답변해야 합니다.

[추천 및 안내 가이드]
- 아래 제공되는 [관광 정보 컨텍스트] 및 [커뮤니티 게시글 컨텍스트]를 참고하여 질문에 성실히 답변하십시오.
- 답변은 자연스러운 한국어 존댓말로 작성하십시오.
"""

async def get_chatbot_reply(db: Session, message: str, history: list[ChatMessage]) -> ChatResponse:
    """
    사용자의 메시지와 대화 이력을 바탕으로 OpenAI API를 호출하여 답변을 생성하고,
    답변의 근거가 되는 장소 및 게시글 목록을 매칭하여 반환합니다.
    """
    # 1. 자연어 분석 및 검색어 추출
    sigungu_code, content_type_id, search_posts_flag, keywords = analyze_message(message)

    # 2. 관련 데이터베이스 조회 (컨텍스트 확보)
    locations = search_locations(db, sigungu_code=sigungu_code, content_type_id=content_type_id, keywords=keywords, limit=5)
    posts = []
    if search_posts_flag or "글" in message or "후기" in message or "리뷰" in message:
        posts = search_posts(db, keywords=keywords, limit=5)

    # 3. 프롬프트 내에 주입할 컨텍스트 텍스트 작성
    context_parts = []
    
    if locations:
        context_parts.append("[관광 정보 컨텍스트]")
        for loc in locations:
            sigungu_name = SIGUNGU_NAMES.get(loc.l_dong_signgu_cd, "서울")
            type_name = CONTENT_TYPE_NAMES.get(loc.content_type_id, "정보")
            context_parts.append(
                f"- 장소명: {loc.title} (ID: {loc.content_id}, 유형: {type_name}, 자치구: {sigungu_name})\n"
                f"  주소: {loc.addr1 or '정보 없음'}\n"
                f"  전화번호: {loc.tel or '정보 없음'}"
            )
            
    if posts:
        context_parts.append("\n[커뮤니티 게시글 컨텍스트]")
        for post in posts:
            context_parts.append(
                f"- 제목: {post.title} (ID: {post.id}, 카테고리: {post.category})\n"
                f"  내용: {post.content[:200]}"
            )

    context_str = "\n".join(context_parts)

    # 4. OpenAI API 요청 메시지 구성
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # 10턴 이내로 history 제한 (사용자 메시지 1 + 에이전트 1 = 1턴이므로 최근 20개 항목 슬라이싱)
    recent_history = history[-20:] if history else []
    for h in recent_history:
        messages.append({"role": h.role, "content": h.content})
        
    # 사용자 질문 구성 (컨텍스트 주입)
    user_prompt = f"질문: {message}"
    if context_str:
        user_prompt = f"{context_str}\n\n위 데이터를 기반으로 아래 질문에 답하세요.\n질문: {message}"
        
    messages.append({"role": "user", "content": user_prompt})

    # 5. OpenAI API 호출 및 예외 처리
    try:
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your_openai_api_key_here":
            # API 키가 설정되지 않은 개발 초기/기본 상태인 경우의 가짜 응답 처리 (테스트 등 대비)
            raise ValueError("OpenAI API Key is not set or placeholder.")
            
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            timeout=30.0  # 타임아웃 30초 명세 적용
        )
        reply_text = response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"OpenAI API call failed: {str(e)}")
        # 명세서 1.4절 공통 에러 응답 규격 적용
        raise HTTPException(
            status_code=502,
            detail={
                "code": "CHATBOT_UPSTREAM_ERROR",
                "message": "OpenAI API 호출에 실패하였습니다. API 키 또는 네트워크 상태를 확인하세요."
            }
        )

    # 6. 답변 텍스트 분석하여 참조(references, post_references) 필터링
    # 답변 텍스트 내에 언급되었거나, 컨텍스트에 포함된 것들을 매칭
    references = []
    for loc in locations:
        # 답변 본문에 장소명이 언급되었는지 확인
        if loc.title in reply_text or loc.content_id in reply_text:
            references.append(LocationRef(
                content_id=loc.content_id,
                content_type_id=loc.content_type_id,
                title=loc.title,
                addr1=loc.addr1
            ))
            
    # 본문 매칭이 없는 경우에도 검색된 상위 1~2개 후보군을 기본 추천 목록에 편입
    if not references and locations:
        references.append(LocationRef(
            content_id=locations[0].content_id,
            content_type_id=locations[0].content_type_id,
            title=locations[0].title,
            addr1=locations[0].addr1
        ))

    post_references = []
    for post in posts:
        # 답변 본문에 게시글 제목이나 ID가 언급되었는지 확인
        if post.title in reply_text or f"ID: {post.id}" in reply_text:
            post_references.append(PostRef(
                id=post.id,
                category=post.category,
                title=post.title
            ))

    return ChatResponse(
        reply=reply_text,
        references=references,
        post_references=post_references
    )
