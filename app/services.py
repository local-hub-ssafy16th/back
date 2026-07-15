import re
from sqlalchemy.orm import Session
from sqlalchemy import or_
from . import models

# 자치구 매핑 테이블 (코드 및 한국어 자치구명)
SIGUNGU_MAP = {
    "종로구": "110", "종로": "110",
    "중구": "140",
    "용산구": "170", "용산": "170",
    "성동구": "200", "성동": "200",
    "광진구": "215", "광진": "215",
    "동대문구": "230", "동대문": "230",
    "중랑구": "260", "중랑": "260",
    "성북구": "290", "성북": "290",
    "강북구": "305", "강북": "305",
    "도봉구": "320", "도봉": "320",
    "노원구": "350", "노원": "350",
    "은평구": "380", "은평": "380",
    "서대문구": "410", "서대문": "410",
    "마포구": "440", "마포": "440",
    "양천구": "470", "양천": "470",
    "강서구": "500", "강서": "500",
    "구로구": "530", "구로": "530",
    "금천구": "545", "금천": "545",
    "영등포구": "560", "영등포": "560",
    "동작구": "590", "동작": "590",
    "관악구": "620", "관악": "620",
    "서초구": "650", "서초": "650",
    "강남구": "680", "강남": "680",
    "송파구": "710", "송파": "710",
    "강동구": "740", "강동": "740",
}

# 콘텐츠 유형 매핑 테이블 (코드 및 키워드)
CONTENT_TYPE_MAP = {
    "관광지": "12", "관광": "12", "명소": "12",
    "문화시설": "14", "문화": "14", "박물관": "14", "미술관": "14",
    "축제공연행사": "15", "축제": "15", "공연": "15", "행사": "15",
    "여행코스": "25", "코스": "25", "여행": "25",
    "레포츠": "28", "레저": "28", "스포츠": "28",
    "숙박": "32", "호텔": "32", "펜션": "32", "모텔": "32", "숙소": "32",
    "쇼핑": "38", "상점": "38", "시장": "38", "마트": "38",
    "음식점": "39", "맛집": "39", "식당": "39", "카페": "39", "음식": "39"
}

CONTENT_TYPE_NAMES = {
    "12": "관광지",
    "14": "문화시설",
    "15": "축제공연행사",
    "25": "여행코스",
    "28": "레포츠",
    "32": "숙박",
    "38": "쇼핑",
    "39": "음식점",
}

SIGUNGU_NAMES = {
    "110": "종로구", "140": "중구", "170": "용산구", "200": "성동구",
    "215": "광진구", "230": "동대문구", "260": "중랑구", "290": "성북구",
    "305": "강북구", "320": "도봉구", "350": "노원구", "380": "은평구",
    "410": "서대문구", "440": "마포구", "470": "양천구", "500": "강서구",
    "530": "구로구", "545": "금천구", "560": "영등포구", "590": "동작구",
    "620": "관악구", "650": "서초구", "680": "강남구", "710": "송파구",
    "740": "강동구"
}

def analyze_message(message: str) -> tuple[str | None, str | None, bool, list[str]]:
    """
    사용자의 입력 메시지(질문)를 분석하여 자치구 코드, 콘텐츠 유형 ID, 
    커뮤니티 게시글 검색 여부, 그리고 검색어 리스트를 추출합니다.
    """
    # 1. 자치구 매핑 확인
    sigungu_code = None
    for name, code in SIGUNGU_MAP.items():
        if name in message:
            sigungu_code = code
            break

    # 2. 콘텐츠 유형 매핑 확인
    content_type_id = None
    for name, cid in CONTENT_TYPE_MAP.items():
        if name in message:
            content_type_id = cid
            break

    # 3. 커뮤니티 게시글 관련 유도 키워드가 포함되어 있는지 판별
    search_posts = False
    post_indicators = ["게시글", "게시판", "글", "후기", "리뷰", "사람들", "커뮤니티"]
    for indicator in post_indicators:
        if indicator in message:
            search_posts = True
            break

    # 4. 단순 검색용 키워드 추출 (특수문자 제외 및 불필요 단어 정제)
    # 띄어쓰기 기준으로 나누어 분석하되, 자치구명, 카테고리명, 지시형 단어는 제외
    words = re.split(r'\s+', message)
    keywords = []
    exclude_keywords = set(list(SIGUNGU_MAP.keys()) + list(CONTENT_TYPE_MAP.keys()) + post_indicators + [
        "추천", "알려줘", "알려", "보여줘", "있니", "있어", "어디", "추천해줘", "어때", "안녕", "안녕하세요"
    ])

    for w in words:
        w_clean = re.sub(r'[^a-zA-Z0-9가-힣]', '', w)
        if len(w_clean) >= 2 and w_clean not in exclude_keywords:
            keywords.append(w_clean)

    return sigungu_code, content_type_id, search_posts, keywords


def search_locations(db: Session, sigungu_code: str = None, content_type_id: str = None, keywords: list[str] = None, limit: int = 5):
    """
    분석된 조건을 기반으로 locations 테이블에서 매칭되는 정보를 최대 N건 검색합니다.
    """
    query = db.query(models.Location)
    
    if sigungu_code:
        query = query.filter(models.Location.l_dong_signgu_cd == sigungu_code)
    
    if content_type_id:
        query = query.filter(models.Location.content_type_id == content_type_id)
        
    if keywords:
        filters = []
        for kw in keywords:
            # 제목 또는 주소1에 포함되는지 확인
            filters.append(models.Location.title.ilike(f"%{kw}%"))
            filters.append(models.Location.addr1.ilike(f"%{kw}%"))
        if filters:
            query = query.filter(or_(*filters))
            
    # 제목 오름차순 정렬
    query = query.order_by(models.Location.title.asc())
    
    return query.limit(limit).all()


def search_posts(db: Session, keywords: list[str] = None, limit: int = 5):
    """
    분석된 조건을 기반으로 posts 테이블에서 매칭되는 글을 최대 N건 검색합니다.
    """
    query = db.query(models.Post)
    
    if keywords:
        filters = []
        for kw in keywords:
            filters.append(models.Post.title.ilike(f"%{kw}%"))
            filters.append(models.Post.content.ilike(f"%{kw}%"))
        if filters:
            query = query.filter(or_(*filters))
            
    # 작성 시간 기준 최신순 정렬
    query = query.order_by(models.Post.created_at.desc())
    
    return query.limit(limit).all()
