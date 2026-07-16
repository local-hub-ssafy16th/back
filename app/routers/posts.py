import math
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile
from sqlalchemy.orm import Session

from .. import schemas
from ..config import settings
from ..constants import CATEGORIES, SEARCH_SCOPES, SORT_OPTIONS
from ..deps import PageParams, get_db, optional_client_id, page_params, required_client_id
from ..errors import (
    image_limit_exceeded,
    image_not_found,
    invalid_parameter,
    password_mismatch,
    post_not_found,
)
from ..images import validate_and_process_image
from ..models import Post, PostImage, PostLike, PostView

posts_router = APIRouter(prefix="/posts", tags=["posts"])
posts_v2_router = APIRouter(prefix="/v2/posts", tags=["posts-v2"])


def _get_post_or_404(db: Session, post_id: int) -> Post:
    post = db.query(Post).filter(Post.id == post_id).first()
    if post is None:
        raise post_not_found()
    return post


def _serialize_post_detail(db: Session, post: Post, liked: bool) -> schemas.PostDetail:
    images = (
        db.query(PostImage)
        .filter(PostImage.post_id == post.id)
        .order_by(PostImage.sort_order.asc())
        .all()
    )
    detail = schemas.PostDetail.model_validate(post)
    detail.liked = liked
    detail.images = [
        schemas.ImageMeta(
            id=img.id,
            url=f"/api/posts/{post.id}/images/{img.id}",
            filename=img.filename,
            content_type=img.content_type,
            size_bytes=img.size_bytes,
            width=img.width,
            height=img.height,
            sort_order=img.sort_order,
        )
        for img in images
    ]
    return detail


# ---------------------------------------------------------------------------
# /api/v2/posts — 목록/상세/작성/수정
# ---------------------------------------------------------------------------


@posts_v2_router.get("", response_model=schemas.PostListResponse)
def list_posts(
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    search_scope: str = "all",
    sort: str = "latest",
    pagination: PageParams = Depends(page_params),
    db: Session = Depends(get_db),
):
    if category is not None and category not in CATEGORIES:
        raise invalid_parameter("정의되지 않은 category 입니다.")
    if search_scope not in SEARCH_SCOPES:
        raise invalid_parameter("정의되지 않은 search_scope 입니다.")
    if sort not in SORT_OPTIONS:
        raise invalid_parameter("정의되지 않은 sort 입니다.")

    query = db.query(Post)
    if category is not None:
        query = query.filter(Post.category == category)
    if keyword:
        like = f"%{keyword}%"
        if search_scope == "title":
            query = query.filter(Post.title.ilike(like))
        elif search_scope == "content":
            query = query.filter(Post.content.ilike(like))
        else:
            query = query.filter((Post.title.ilike(like)) | (Post.content.ilike(like)))

    total = query.count()
    total_pages = math.ceil(total / pagination.size) if total else 0

    if sort == "views":
        order = (Post.view_count.desc(), Post.created_at.desc())
    elif sort == "likes":
        order = (Post.like_count.desc(), Post.created_at.desc())
    elif sort == "comments":
        order = (Post.comment_count.desc(), Post.created_at.desc())
    else:
        order = (Post.created_at.desc(), Post.id.desc())

    rows = query.order_by(*order).offset(pagination.offset).limit(pagination.size).all()

    thumbnails: dict[int, PostImage] = {}
    post_ids = [row.id for row in rows]
    if post_ids:
        imgs = (
            db.query(PostImage)
            .filter(PostImage.post_id.in_(post_ids))
            .order_by(PostImage.post_id, PostImage.sort_order.asc())
            .all()
        )
        for img in imgs:
            thumbnails.setdefault(img.post_id, img)

    items = []
    for row in rows:
        item = schemas.PostListItem.model_validate(row)
        thumb = thumbnails.get(row.id)
        item.thumbnail_url = f"/api/posts/{row.id}/images/{thumb.id}" if thumb else None
        items.append(item)

    return schemas.PostListResponse(
        items=items,
        page=pagination.page,
        size=pagination.size,
        total=total,
        total_pages=total_pages,
    )


@posts_v2_router.get("/{post_id}", response_model=schemas.PostDetail)
def get_post(
    post_id: int,
    client_id: Optional[str] = Depends(optional_client_id),
    db: Session = Depends(get_db),
):
    post = _get_post_or_404(db, post_id)

    if client_id:
        existing_view = (
            db.query(PostView)
            .filter(PostView.post_id == post_id, PostView.client_id == client_id)
            .first()
        )
        if existing_view is None:
            db.add(PostView(post_id=post_id, client_id=client_id))
            post.view_count = post.view_count + 1
            db.commit()
            db.refresh(post)

    liked = False
    if client_id:
        liked = (
            db.query(PostLike)
            .filter(PostLike.post_id == post_id, PostLike.client_id == client_id)
            .first()
            is not None
        )

    return _serialize_post_detail(db, post, liked=liked)


@posts_v2_router.post("", response_model=schemas.PostDetail, status_code=201)
async def create_post(
    category: str = Form(...),
    title: str = Form(..., min_length=1, max_length=200),
    content: str = Form(..., min_length=1, max_length=5000),
    password: str = Form(..., min_length=4, max_length=20),
    images: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
):
    if category not in CATEGORIES:
        raise invalid_parameter("정의되지 않은 category 입니다.")
    if len(images) > settings.max_images_per_post:
        raise image_limit_exceeded()

    processed = [validate_and_process_image(upload, await upload.read()) for upload in images]

    post = Post(category=category, title=title, content=content, password=password)
    db.add(post)
    db.flush()

    for sort_order, item in enumerate(processed):
        db.add(
            PostImage(
                post_id=post.id,
                filename=item.filename,
                content_type=item.content_type,
                size_bytes=item.size_bytes,
                width=item.width,
                height=item.height,
                data=item.data,
                sort_order=sort_order,
            )
        )

    db.commit()
    db.refresh(post)
    return _serialize_post_detail(db, post, liked=False)


@posts_v2_router.put("/{post_id}", response_model=schemas.PostDetail)
async def update_post(
    post_id: int,
    title: str = Form(..., min_length=1, max_length=200),
    content: str = Form(..., min_length=1, max_length=5000),
    password: str = Form(..., min_length=4, max_length=20),
    keep_image_ids: str = Form(default=""),
    images: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
):
    post = _get_post_or_404(db, post_id)
    if post.password != password:
        raise password_mismatch()

    try:
        keep_ids = [int(x) for x in keep_image_ids.split(",") if x.strip()]
    except ValueError:
        raise invalid_parameter("keep_image_ids 형식이 올바르지 않습니다.")

    existing_images = db.query(PostImage).filter(PostImage.post_id == post_id).all()
    existing_ids = {img.id for img in existing_images}
    if not set(keep_ids).issubset(existing_ids):
        raise invalid_parameter("keep_image_ids에 해당 게시글 소유가 아닌 이미지 ID가 포함되어 있습니다.")

    if len(keep_ids) + len(images) > settings.max_images_per_post:
        raise image_limit_exceeded()

    processed = [validate_and_process_image(upload, await upload.read()) for upload in images]

    kept_images = [img for img in existing_images if img.id in keep_ids]
    for img in existing_images:
        if img.id not in keep_ids:
            db.delete(img)

    next_sort_order = max((img.sort_order for img in kept_images), default=-1) + 1
    for offset, item in enumerate(processed):
        db.add(
            PostImage(
                post_id=post_id,
                filename=item.filename,
                content_type=item.content_type,
                size_bytes=item.size_bytes,
                width=item.width,
                height=item.height,
                data=item.data,
                sort_order=next_sort_order + offset,
            )
        )

    post.title = title
    post.content = content
    post.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(post)
    return _serialize_post_detail(db, post, liked=False)


# ---------------------------------------------------------------------------
# /api/posts — verify / delete / like / images (v1 URL 유지 + 신규)
# ---------------------------------------------------------------------------


@posts_router.post("/{post_id}/verify", response_model=schemas.VerifyResponse)
def verify_password(post_id: int, body: schemas.PasswordVerify, db: Session = Depends(get_db)):
    post = _get_post_or_404(db, post_id)
    if post.password != body.password:
        raise password_mismatch()
    return schemas.VerifyResponse(verified=True)


@posts_router.delete("/{post_id}", status_code=204)
def delete_post(post_id: int, body: schemas.PostDelete, db: Session = Depends(get_db)):
    post = _get_post_or_404(db, post_id)
    if post.password != body.password:
        raise password_mismatch()

    db.delete(post)
    db.commit()
    return Response(status_code=204)


@posts_router.post("/{post_id}/like", response_model=schemas.LikeResponse)
def like_post(
    post_id: int,
    client_id: str = Depends(required_client_id),
    db: Session = Depends(get_db),
):
    post = _get_post_or_404(db, post_id)
    existing = (
        db.query(PostLike)
        .filter(PostLike.post_id == post_id, PostLike.client_id == client_id)
        .first()
    )
    if existing is None:
        db.add(PostLike(post_id=post_id, client_id=client_id))
        post.like_count = post.like_count + 1
        db.commit()

    return schemas.LikeResponse(post_id=post_id, like_count=post.like_count, liked=True)


@posts_router.delete("/{post_id}/like", response_model=schemas.LikeResponse)
def unlike_post(
    post_id: int,
    client_id: str = Depends(required_client_id),
    db: Session = Depends(get_db),
):
    post = _get_post_or_404(db, post_id)
    existing = (
        db.query(PostLike)
        .filter(PostLike.post_id == post_id, PostLike.client_id == client_id)
        .first()
    )
    if existing is not None:
        db.delete(existing)
        post.like_count = max(post.like_count - 1, 0)
        db.commit()

    return schemas.LikeResponse(post_id=post_id, like_count=post.like_count, liked=False)


@posts_router.get("/{post_id}/images/{image_id}")
def get_post_image(post_id: int, image_id: int, db: Session = Depends(get_db)):
    _get_post_or_404(db, post_id)
    image = (
        db.query(PostImage)
        .filter(PostImage.id == image_id, PostImage.post_id == post_id)
        .first()
    )
    if image is None:
        raise image_not_found()
    return Response(
        content=image.data,
        media_type=image.content_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )
