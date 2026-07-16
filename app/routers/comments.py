import math
from datetime import datetime

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from .. import schemas
from ..deps import PageParams, get_db, page_params
from ..errors import comment_not_found, password_mismatch, post_not_found
from ..models import Comment, Post

post_comments_router = APIRouter(prefix="/posts", tags=["comments"])
comments_router = APIRouter(prefix="/comments", tags=["comments"])


def _get_post_or_404(db: Session, post_id: int) -> Post:
    post = db.query(Post).filter(Post.id == post_id).first()
    if post is None:
        raise post_not_found()
    return post


def _get_comment_or_404(db: Session, comment_id: int) -> Comment:
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if comment is None:
        raise comment_not_found()
    return comment


@post_comments_router.get("/{post_id}/comments", response_model=schemas.CommentListResponse)
def list_comments(
    post_id: int,
    pagination: PageParams = Depends(page_params),
    db: Session = Depends(get_db),
):
    _get_post_or_404(db, post_id)

    query = db.query(Comment).filter(Comment.post_id == post_id)
    total = query.count()
    total_pages = math.ceil(total / pagination.size) if total else 0

    rows = (
        query.order_by(Comment.created_at.asc(), Comment.id.asc())
        .offset(pagination.offset)
        .limit(pagination.size)
        .all()
    )

    return schemas.CommentListResponse(
        items=[schemas.CommentItem.model_validate(row) for row in rows],
        page=pagination.page,
        size=pagination.size,
        total=total,
        total_pages=total_pages,
    )


@post_comments_router.post(
    "/{post_id}/comments", response_model=schemas.CommentItem, status_code=201
)
def create_comment(
    post_id: int, body: schemas.CommentCreate, db: Session = Depends(get_db)
):
    post = _get_post_or_404(db, post_id)

    comment = Comment(post_id=post_id, content=body.content, password=body.password)
    db.add(comment)
    post.comment_count = post.comment_count + 1
    db.commit()
    db.refresh(comment)
    return schemas.CommentItem.model_validate(comment)


@comments_router.post("/{comment_id}/verify", response_model=schemas.VerifyResponse)
def verify_comment_password(
    comment_id: int, body: schemas.PasswordVerify, db: Session = Depends(get_db)
):
    comment = _get_comment_or_404(db, comment_id)
    if comment.password != body.password:
        raise password_mismatch()
    return schemas.VerifyResponse(verified=True)


@comments_router.put("/{comment_id}", response_model=schemas.CommentItem)
def update_comment(
    comment_id: int, body: schemas.CommentUpdate, db: Session = Depends(get_db)
):
    comment = _get_comment_or_404(db, comment_id)
    if comment.password != body.password:
        raise password_mismatch()

    comment.content = body.content
    comment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(comment)
    return schemas.CommentItem.model_validate(comment)


@comments_router.delete("/{comment_id}", status_code=204)
def delete_comment(
    comment_id: int, body: schemas.CommentDelete, db: Session = Depends(get_db)
):
    comment = _get_comment_or_404(db, comment_id)
    if comment.password != body.password:
        raise password_mismatch()

    post = db.query(Post).filter(Post.id == comment.post_id).first()
    db.delete(comment)
    if post is not None:
        post.comment_count = max(post.comment_count - 1, 0)
    db.commit()
    return Response(status_code=204)
