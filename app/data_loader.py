import json
from pathlib import Path

from sqlalchemy.orm import Session

from .config import settings
from .constants import CONTENT_TYPE_FILES
from .models import Location


def _norm(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text != "" else None


def _norm_float(value: object) -> float | None:
    text = _norm(value)
    if text is None:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def load_locations(db: Session) -> int:
    data_dir = Path(settings.data_dir)

    for content_type_id, filename in CONTENT_TYPE_FILES.items():
        file_path = data_dir / filename
        if not file_path.exists():
            continue

        with file_path.open(encoding="utf-8") as f:
            payload = json.load(f)

        for item in payload.get("items", []):
            location = Location(
                content_id=item["contentid"],
                content_type_id=item.get("contenttypeid", content_type_id),
                title=item["title"],
                addr1=_norm(item.get("addr1")),
                addr2=_norm(item.get("addr2")),
                zipcode=_norm(item.get("zipcode")),
                tel=_norm(item.get("tel")),
                mapx=_norm_float(item.get("mapx")),
                mapy=_norm_float(item.get("mapy")),
                mlevel=_norm(item.get("mlevel")),
                l_dong_regn_cd=_norm(item.get("lDongRegnCd")),
                l_dong_signgu_cd=_norm(item.get("lDongSignguCd")),
                lcls_systm1=_norm(item.get("lclsSystm1")),
                lcls_systm2=_norm(item.get("lclsSystm2")),
                lcls_systm3=_norm(item.get("lclsSystm3")),
                firstimage=_norm(item.get("firstimage")),
                firstimage2=_norm(item.get("firstimage2")),
                cpyrht_div_cd=_norm(item.get("cpyrhtDivCd")),
                createdtime=_norm(item.get("createdtime")),
                modifiedtime=_norm(item.get("modifiedtime")),
            )
            db.merge(location)

    db.commit()
    return db.query(Location).count()
