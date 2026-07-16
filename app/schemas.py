from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field

Category = Literal["tour", "food", "festival"]
SearchScope = Literal["title", "content", "all"]
SortOption = Literal["latest", "views", "likes", "comments"]


# ---------- 공통 ----------
class ErrorDetail(BaseModel):
    code: str
    message: str


class Page(BaseModel):
    page: int
    size: int
    total: int
    total_pages: int


class HealthResponse(BaseModel):
    status: str
    region: str
    locations_loaded: int


# ---------- posts ----------
# PostCreate/PostUpdate는 multipart/form-data로 전송되므로 Pydantic 모델이 아닌
# 라우터의 Form/File 파라미터로 직접 선언한다 (명세서 10절 참조).


class PostDelete(BaseModel):
    password: str = Field(min_length=4, max_length=20)


class PasswordVerify(BaseModel):
    password: str = Field(min_length=4, max_length=20)


class ImageMeta(BaseModel):
    id: int
    url: str
    filename: str
    content_type: str
    size_bytes: int
    width: Optional[int] = None
    height: Optional[int] = None
    sort_order: int

    model_config = {"from_attributes": True}


class PostListItem(BaseModel):
    id: int
    category: Category
    title: str
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    thumbnail_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PostDetail(PostListItem):
    content: str  # password 미포함
    liked: bool = False
    images: list[ImageMeta] = []


class PostListResponse(Page):
    items: list[PostListItem]


class VerifyResponse(BaseModel):
    verified: bool


class LikeResponse(BaseModel):
    post_id: int
    like_count: int
    liked: bool


# ---------- comments ----------
class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=1000)
    password: str = Field(min_length=4, max_length=20)


class CommentUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=1000)
    password: str = Field(min_length=4, max_length=20)


class CommentDelete(BaseModel):
    password: str = Field(min_length=4, max_length=20)


class CommentItem(BaseModel):
    id: int
    post_id: int
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CommentListResponse(Page):
    items: list[CommentItem]


# ---------- locations ----------
class LocationListItem(BaseModel):
    content_id: str
    content_type_id: str
    content_type_name: str
    title: str
    addr1: Optional[str] = None
    addr2: Optional[str] = None
    sigungu_name: Optional[str] = None
    firstimage: Optional[str] = None
    firstimage2: Optional[str] = None
    mapx: Optional[float] = None
    mapy: Optional[float] = None

    model_config = {"from_attributes": True}


class DataSource(BaseModel):
    provider: str = "한국관광공사"
    dataset: str = "국문 관광정보 서비스 (TourAPI 4.0)"
    url: str = "https://www.data.go.kr/data/15101578/openapi.do"
    license: str = "공공누리 제3유형"


class LocationDetail(LocationListItem):
    zipcode: Optional[str] = None
    tel: Optional[str] = None
    mlevel: Optional[str] = None
    l_dong_regn_cd: Optional[str] = None
    l_dong_signgu_cd: Optional[str] = None
    lcls_systm1: Optional[str] = None
    lcls_systm2: Optional[str] = None
    lcls_systm3: Optional[str] = None
    cpyrht_div_cd: Optional[str] = None
    createdtime: Optional[str] = None
    modifiedtime: Optional[str] = None
    source: DataSource = DataSource()


class LocationListResponse(Page):
    items: list[LocationListItem]


class CategoryMetaItem(BaseModel):
    content_type_id: str
    name: str
    count: int
    available: bool


class CategoryMetaResponse(BaseModel):
    items: list[CategoryMetaItem]
    total: int


class SigunguMetaItem(BaseModel):
    code: str
    name: str
    count: int


class SigunguMetaResponse(BaseModel):
    items: list[SigunguMetaItem]
    total: int


# ---------- chat ----------
class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    history: list[ChatMessage] = []


class LocationRef(BaseModel):
    content_id: str
    content_type_id: str
    title: str
    addr1: Optional[str] = None


class PostRef(BaseModel):
    id: int
    category: Category
    title: str


class ChatResponse(BaseModel):
    reply: str
    references: list[LocationRef] = []
    post_references: list[PostRef] = []
