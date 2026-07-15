from sqlalchemy import Column, DateTime, Float, Index, Integer, String, Text, func

from .database import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(20), nullable=False)  # tour | food | festival
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    password = Column(String(100), nullable=False)  # 평문 저장 (의도된 설계)
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())

    __table_args__ = (
        Index("ix_posts_category", "category"),
        Index("ix_posts_created_at", "created_at"),
    )


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
