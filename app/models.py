from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    func,
)
from .database import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(20), nullable=False)  # tour | food | festival
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    password = Column(String(100), nullable=False)  # 평문 저장 (의도된 설계)
    view_count = Column(Integer, nullable=False, server_default="0")
    like_count = Column(Integer, nullable=False, server_default="0")
    comment_count = Column(Integer, nullable=False, server_default="0")
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())

    __table_args__ = (
        Index("ix_posts_category", "category"),
        Index("ix_posts_created_at", "created_at"),
        Index("ix_posts_view_count", "view_count"),
        Index("ix_posts_like_count", "like_count"),
    )


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    password = Column(String(100), nullable=False)  # 평문 저장 (게시글과 동일 정책)
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())

    __table_args__ = (Index("ix_comments_post_id", "post_id", "created_at"),)


class PostLike(Base):
    __tablename__ = "post_likes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    client_id = Column(String(36), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())

    __table_args__ = (
        UniqueConstraint("post_id", "client_id"),
        Index("ix_post_likes_post_id", "post_id"),
    )


class PostView(Base):
    __tablename__ = "post_views"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    client_id = Column(String(36), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())

    __table_args__ = (
        UniqueConstraint("post_id", "client_id"),
        Index("ix_post_views_post_id", "post_id"),
    )


class PostImage(Base):
    __tablename__ = "post_images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(50), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    width = Column(Integer)
    height = Column(Integer)
    data = Column(LargeBinary, nullable=False)
    sort_order = Column(Integer, nullable=False, server_default="0")
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())

    __table_args__ = (Index("ix_post_images_post_id", "post_id", "sort_order"),)


class Location(Base):
    __tablename__ = "locations"

    content_id = Column(String(20), primary_key=True)
    content_type_id = Column(String(5), nullable=False)
    title = Column(String(300), nullable=False)
    addr1 = Column(String(300))
    addr2 = Column(String(300))
    zipcode = Column(String(20))
    tel = Column(String(100))
    mapx = Column(Float)
    mapy = Column(Float)
    mlevel = Column(String(5))
    l_dong_regn_cd = Column(String(5))
    l_dong_signgu_cd = Column(String(5))
    lcls_systm1 = Column(String(10))
    lcls_systm2 = Column(String(10))
    lcls_systm3 = Column(String(20))
    firstimage = Column(String(500))
    firstimage2 = Column(String(500))
    cpyrht_div_cd = Column(String(10))
    createdtime = Column(String(14))
    modifiedtime = Column(String(14))

    __table_args__ = (
        Index("ix_locations_type", "content_type_id"),
        Index("ix_locations_signgu", "l_dong_signgu_cd"),
        Index("ix_locations_title", "title"),
    )
