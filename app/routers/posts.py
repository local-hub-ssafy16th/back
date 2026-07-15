import math
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from .. import schemas
from ..constants import CATEGORIES
from ..deps import PageParams, get_db, page_params
from ..errors import invalid_parameter, password_mismatch, post_not_found
from ..models import Post

router = APIRouter(prefix="/posts", tags=["posts"])


def _get_post_or_404(db: Session, post_id: int) -> Post:
    post = db.query(Post).filter(Post.id == post_id).first()
    if post is None:
        raise post_not_found()
    return post


@router.get("", response_model=schemas.PostListResponse)
def list_posts(
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    pagination: PageParams = Depends(page_params),
    db: Session = Depends(get_db),
):
    if category is not None and category not in CATEGORIES:
        raise invalid_parameter("정의되지 않은 category 입니다.")

    query = db.query(Post)
    if category is not None:
        query = query.filter(Post.category == category)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter((Post.title.ilike(like)) | (Post.content.ilike(like)))

    total = query.count()
    total_pages = math.ceil(total / pagination.size) if total else 0

    rows = (
        query.order_by(Post.created_at.desc(), Post.id.desc())
        .offset(pagination.offset)
        .limit(pagination.size)
        .all()
    )

    return schemas.PostListResponse(
        items=[schemas.PostListItem.model_validate(row) for row in rows],
        page=pagination.page,
        size=pagination.size,
        total=total,
        total_pages=total_pages,
    )


@router.get("/{post_id}", response_model=schemas.PostDetail)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = _get_post_or_404(db, post_id)
    return schemas.PostDetail.model_validate(post)


@router.post("", response_model=schemas.PostDetail, status_code=201)
def create_post(body: schemas.PostCreate, db: Session = Depends(get_db)):
    if body.category not in CATEGORIES:
        raise invalid_parameter("정의되지 않은 category 입니다.")

    post = Post(
        category=body.category,
        title=body.title,
        content=body.content,
        password=body.password,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return schemas.PostDetail.model_validate(post)


@router.post("/{post_id}/verify", response_model=schemas.VerifyResponse)
def verify_password(post_id: int, body: schemas.PasswordVerify, db: Session = Depends(get_db)):
    post = _get_post_or_404(db, post_id)
    if post.password != body.password:
        raise password_mismatch()
    return schemas.VerifyResponse(verified=True)


@router.put("/{post_id}", response_model=schemas.PostDetail)
def update_post(post_id: int, body: schemas.PostUpdate, db: Session = Depends(get_db)):
    post = _get_post_or_404(db, post_id)
    if post.password != body.password:
        raise password_mismatch()

    post.title = body.title
    post.content = body.content
    post.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(post)
    return schemas.PostDetail.model_validate(post)


@router.delete("/{post_id}", status_code=204)
def delete_post(post_id: int, body: schemas.PostDelete, db: Session = Depends(get_db)):
    post = _get_post_or_404(db, post_id)
    if post.password != body.password:
        raise password_mismatch()

    db.delete(post)
    db.commit()
    return Response(status_code=204)
