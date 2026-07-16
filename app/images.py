import io
from dataclasses import dataclass
from typing import Optional

from fastapi import UploadFile
from PIL import Image, ImageOps

from .config import settings
from .errors import image_too_large, unsupported_image_type

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}

_FORMAT_BY_CONTENT_TYPE = {
    "image/jpeg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP",
}


@dataclass
class ProcessedImage:
    filename: str
    content_type: str
    data: bytes
    size_bytes: int
    width: Optional[int]
    height: Optional[int]


def validate_and_process_image(upload_file: UploadFile, raw_data: bytes) -> ProcessedImage:
    content_type = upload_file.content_type
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise unsupported_image_type()

    max_bytes = settings.max_image_size_mb * 1024 * 1024
    if len(raw_data) > max_bytes:
        raise image_too_large()

    try:
        image = Image.open(io.BytesIO(raw_data))
        image.load()
    except Exception:
        raise unsupported_image_type()

    original_format = image.format
    image = ImageOps.exif_transpose(image)

    max_dimension = settings.image_max_dimension
    if max(image.width, image.height) > max_dimension:
        image.thumbnail((max_dimension, max_dimension), Image.LANCZOS)

    save_format = original_format or _FORMAT_BY_CONTENT_TYPE[content_type]
    if save_format == "JPEG" and image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    output = io.BytesIO()
    image.save(output, format=save_format)
    data = output.getvalue()

    return ProcessedImage(
        filename=upload_file.filename or "image",
        content_type=content_type,
        data=data,
        size_bytes=len(data),
        width=image.width,
        height=image.height,
    )
