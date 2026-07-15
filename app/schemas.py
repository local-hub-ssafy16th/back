from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

Category = Literal["tour", "food", "festival"]


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
class PostBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=5000)


class PostCreate(PostBase):
    # 명세서 9절은 Literal(Category)을 사용하지만, 그렇게 하면 FastAPI가 미정의 category를
    # 422로 자동 거부해 6.3절이 명시한 "400 INVALID_PARAMETER" 계약과 충돌한다.
    # 계약을 지키기 위해 str로 받고 라우터에서 직접 400을 발생시킨다.
    category: str
    password: str = Field(min_length=4, max_length=20)


class PostUpdate(PostBase):
    password: str = Field(min_length=4, max_length=20)


class PostDelete(BaseModel):
    password: str = Field(min_length=4, max_length=20)


class PasswordVerify(BaseModel):
    password: str = Field(min_length=4, max_length=20)


class PostListItem(BaseModel):
    id: int
    category: Category
    title: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class PostDetail(PostListItem):
    content: str  # password 미포함


class PostListResponse(Page):
    items: list[PostListItem]


class VerifyResponse(BaseModel):
    verified: bool


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
