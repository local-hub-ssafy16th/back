from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.sql import func
from .database import Base


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(20), nullable=False, index=True)  # tour | food | festival
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    password = Column(String(100), nullable=False)  # Plain text comparison
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class Location(Base):
    __tablename__ = "locations"

    content_id = Column(String(20), primary_key=True)  # contentid
    content_type_id = Column(String(5), nullable=False, index=True)  # contenttypeid
    title = Column(String(300), nullable=False, index=True)
    addr1 = Column(String(300), nullable=True)
    addr2 = Column(String(300), nullable=True)
    zipcode = Column(String(20), nullable=True)
    tel = Column(String(100), nullable=True)
    mapx = Column(Float, nullable=True)  # string -> float conversion
    mapy = Column(Float, nullable=True)
    mlevel = Column(String(5), nullable=True)
    l_dong_regn_cd = Column(String(5), nullable=True)  # Seoul = 11
    l_dong_signgu_cd = Column(String(5), nullable=True, index=True)  # sigungu
    lcls_systm1 = Column(String(10), nullable=True)
    lcls_systm2 = Column(String(10), nullable=True)
    lcls_systm3 = Column(String(20), nullable=True)
    firstimage = Column(String(500), nullable=True)
    firstimage2 = Column(String(500), nullable=True)
    cpyrht_div_cd = Column(String(10), nullable=True)
    createdtime = Column(String(14), nullable=True)  # YYYYMMDDHHmmss
    modifiedtime = Column(String(14), nullable=True)
