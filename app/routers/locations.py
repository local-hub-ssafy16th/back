import math
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import schemas
from ..constants import CONTENT_TYPE_FILES, CONTENT_TYPE_NAMES, SIGUNGU_NAMES
from ..deps import PageParams, get_db, page_params
from ..errors import invalid_parameter, location_not_found
from ..models import Location

router = APIRouter(prefix="/locations", tags=["locations"])


def _to_list_item(loc: Location) -> schemas.LocationListItem:
    return schemas.LocationListItem(
        content_id=loc.content_id,
        content_type_id=loc.content_type_id,
        content_type_name=CONTENT_TYPE_NAMES.get(loc.content_type_id, loc.content_type_id),
        title=loc.title,
        addr1=loc.addr1,
        addr2=loc.addr2,
        sigungu_name=SIGUNGU_NAMES.get(loc.l_dong_signgu_cd or ""),
        firstimage=loc.firstimage,
        firstimage2=loc.firstimage2,
        mapx=loc.mapx,
        mapy=loc.mapy,
    )


@router.get("", response_model=schemas.LocationListResponse)
def list_locations(
    content_type_id: Optional[str] = None,
    sigungu: Optional[str] = None,
    keyword: Optional[str] = None,
    pagination: PageParams = Depends(page_params),
    db: Session = Depends(get_db),
):
    if content_type_id is not None and content_type_id not in CONTENT_TYPE_NAMES:
        raise invalid_parameter("정의되지 않은 content_type_id 입니다.")
    if sigungu is not None and sigungu not in SIGUNGU_NAMES:
        raise invalid_parameter("정의되지 않은 sigungu 코드입니다.")

    query = db.query(Location)
    if content_type_id is not None:
        query = query.filter(Location.content_type_id == content_type_id)
    if sigungu is not None:
        query = query.filter(Location.l_dong_signgu_cd == sigungu)
    if keyword:
        query = query.filter(Location.title.ilike(f"%{keyword}%"))

    total = query.count()
    total_pages = math.ceil(total / pagination.size) if total else 0

    rows = (
        query.order_by(Location.title.asc())
        .offset(pagination.offset)
        .limit(pagination.size)
        .all()
    )

    return schemas.LocationListResponse(
        items=[_to_list_item(row) for row in rows],
        page=pagination.page,
        size=pagination.size,
        total=total,
        total_pages=total_pages,
    )


@router.get("/meta/categories", response_model=schemas.CategoryMetaResponse)
def list_categories(db: Session = Depends(get_db)):
    items = []
    total = 0
    for content_type_id, name in CONTENT_TYPE_NAMES.items():
        count = db.query(Location).filter(Location.content_type_id == content_type_id).count()
        total += count
        items.append(
            schemas.CategoryMetaItem(
                content_type_id=content_type_id,
                name=name,
                count=count,
                available=content_type_id in CONTENT_TYPE_FILES,
            )
        )
    return schemas.CategoryMetaResponse(items=items, total=total)


@router.get("/meta/sigungu", response_model=schemas.SigunguMetaResponse)
def list_sigungu(db: Session = Depends(get_db)):
    items = []
    for code in sorted(SIGUNGU_NAMES, key=int):
        count = db.query(Location).filter(Location.l_dong_signgu_cd == code).count()
        items.append(schemas.SigunguMetaItem(code=code, name=SIGUNGU_NAMES[code], count=count))
    return schemas.SigunguMetaResponse(items=items, total=len(items))


@router.get("/{content_id}", response_model=schemas.LocationDetail)
def get_location(content_id: str, db: Session = Depends(get_db)):
    loc = db.query(Location).filter(Location.content_id == content_id).first()
    if loc is None:
        raise location_not_found()

    return schemas.LocationDetail(
        **_to_list_item(loc).model_dump(),
        zipcode=loc.zipcode,
        tel=loc.tel,
        mlevel=loc.mlevel,
        l_dong_regn_cd=loc.l_dong_regn_cd,
        l_dong_signgu_cd=loc.l_dong_signgu_cd,
        lcls_systm1=loc.lcls_systm1,
        lcls_systm2=loc.lcls_systm2,
        lcls_systm3=loc.lcls_systm3,
        cpyrht_div_cd=loc.cpyrht_div_cd,
        createdtime=loc.createdtime,
        modifiedtime=loc.modifiedtime,
    )
