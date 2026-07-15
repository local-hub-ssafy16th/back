import random

from sqlalchemy.orm import Session

from .models import Location, Post

SEED_PASSWORD = "1234"

# {title}/{addr} 는 locations 테이블의 실제 title/addr1로 채워진다.
TOUR_TEMPLATES = [
    ("{title} 다녀왔어요, 완전 만족!", "{addr} 근처였는데 생각보다 볼거리가 많았어요. 다음에 또 가고 싶네요."),
    ("{title} 근처 주차 팁 공유합니다", "{addr} 쪽으로 가시면 골목 안쪽에 공영주차장이 있더라고요. 참고하세요!"),
    ("{title} 데이트 코스로 괜찮을까요?", "{addr} 근처인데 분위기 좋은 곳 찾다가 발견했어요. 가보신 분 후기 부탁드려요."),
    ("{title} 사진 찍기 좋은 스팟인가요", "얼마 전 {addr} 지나가다가 봤는데 사진 찍기 좋아 보이더라고요."),
    ("{title} 평일 오전에 한적한가요?", "주말엔 사람 많을 것 같은데 평일 오전 방문 계획 중입니다. 다녀오신 분 계세요?"),
]

# 축제 일정(날짜) 데이터가 없으므로(2.3절) 날짜를 언급하지 않는다.
FESTIVAL_TEMPLATES = [
    ("{title} 위치 공유합니다", "{addr} 근처에서 열리는 것 같아요. 다녀오신 분 분위기 어떤지 궁금합니다."),
    ("{title} 가보신 분 계신가요?", "{addr} 쪽인데 아이 데리고 가도 괜찮을까요?"),
    ("{title} 근처 맛집도 같이 다녀오기 좋을까요", "{addr} 근처라 같이 묶어서 다녀오면 좋을 것 같아서요."),
    ("{title} 볼거리 많나요?", "{addr}에서 하는 걸로 보이는데 규모가 어느 정도인지 아시는 분?"),
    ("{title} 다녀온 후기 남겨요", "{addr} 쪽 다녀왔는데 생각보다 사람이 많더라고요. 여유 있게 가시는 걸 추천해요."),
]

# 음식점 원본 데이터가 없으므로(2.3절) 특정 장소를 언급하지 않는 일반 게시글로 구성.
FOOD_POSTS = [
    ("이 동네 혼밥하기 좋은 곳 있을까요?", "이사온 지 얼마 안 돼서 아직 맛집을 잘 몰라요. 혼자 가기 편한 곳 추천 부탁드려요."),
    ("저녁 메뉴 추천 부탁드려요", "매일 뭐 먹을지 고민이네요. 이 동네 숨은 맛집 있으면 알려주세요!"),
    ("배달 안 되는 맛집 아시는 분?", "직접 가야만 먹을 수 있는 맛있는 곳 찾고 있어요."),
    ("가성비 좋은 점심 메뉴 찾습니다", "회사 근처에서 부담없이 먹을 수 있는 곳 알려주시면 감사하겠습니다."),
    ("단체 회식 장소 추천해주세요", "10명 정도 모임인데 룸 있는 곳 아시는 분 계신가요?"),
    ("디저트 맛집 있나요?", "커피랑 디저트 같이 즐길 수 있는 카페 찾고 있어요."),
    ("비 오는 날 생각나는 음식 뭐 드세요?", "오늘같이 비 오는 날엔 뭐가 땡기시나요? 다들 뭐 드시는지 궁금해요."),
    ("야식 맛집 정보 공유해요", "늦은 시간까지 하는 곳 아시는 분 댓글로 알려주세요."),
    ("채식 메뉴 있는 곳 찾아요", "비건/채식 옵션 있는 식당 아시는 분 계신가요?"),
    ("웨이팅 없는 맛집 있을까요?", "항상 줄 서는 곳만 알고 있는데 조용히 갈 수 있는 곳도 궁금해요."),
]


def _sample_locations(db: Session, content_type_id: str, count: int) -> list[Location]:
    rows = (
        db.query(Location)
        .filter(Location.content_type_id == content_type_id, Location.addr1.isnot(None))
        .all()
    )
    if len(rows) <= count:
        return rows
    return random.sample(rows, count)


def seed_initial_posts(db: Session, per_category: int = 10) -> int:
    """게시판이 비어있을 때만(최초 실행 시) 카테고리별 초기 게시글을 채운다."""
    if db.query(Post).count() > 0:
        return 0

    posts: list[Post] = []

    for i, loc in enumerate(_sample_locations(db, "12", per_category)):
        title_tpl, content_tpl = TOUR_TEMPLATES[i % len(TOUR_TEMPLATES)]
        posts.append(
            Post(
                category="tour",
                title=title_tpl.format(title=loc.title, addr=loc.addr1),
                content=content_tpl.format(title=loc.title, addr=loc.addr1),
                password=SEED_PASSWORD,
            )
        )

    for i, loc in enumerate(_sample_locations(db, "15", per_category)):
        title_tpl, content_tpl = FESTIVAL_TEMPLATES[i % len(FESTIVAL_TEMPLATES)]
        posts.append(
            Post(
                category="festival",
                title=title_tpl.format(title=loc.title, addr=loc.addr1),
                content=content_tpl.format(title=loc.title, addr=loc.addr1),
                password=SEED_PASSWORD,
            )
        )

    for title, content in FOOD_POSTS[:per_category]:
        posts.append(Post(category="food", title=title, content=content, password=SEED_PASSWORD))

    db.add_all(posts)
    db.commit()
    return len(posts)
