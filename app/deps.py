import re
from dataclasses import dataclass
from typing import Optional

from fastapi import Header, Query

from .database import SessionLocal
from .errors import client_id_required, invalid_client_id

UUID_V4_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", re.IGNORECASE
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def optional_client_id(
    x_client_id: Optional[str] = Header(default=None, alias="X-Client-Id"),
) -> Optional[str]:
    if x_client_id is None:
        return None
    if not UUID_V4_RE.match(x_client_id):
        raise invalid_client_id()
    return x_client_id


def required_client_id(
    x_client_id: Optional[str] = Header(default=None, alias="X-Client-Id"),
) -> str:
    if x_client_id is None:
        raise client_id_required()
    if not UUID_V4_RE.match(x_client_id):
        raise invalid_client_id()
    return x_client_id


@dataclass
class PageParams:
    page: int
    size: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


def page_params(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
) -> PageParams:
    return PageParams(page=page, size=size)
