from dataclasses import dataclass

from fastapi import Query

from .database import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
