from fastapi import HTTPException


def api_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


def invalid_parameter(message: str) -> HTTPException:
    return api_error(400, "INVALID_PARAMETER", message)


def password_mismatch() -> HTTPException:
    return api_error(403, "PASSWORD_MISMATCH", "비밀번호가 일치하지 않습니다.")


def post_not_found() -> HTTPException:
    return api_error(404, "POST_NOT_FOUND", "게시글을 찾을 수 없습니다.")


def location_not_found() -> HTTPException:
    return api_error(404, "LOCATION_NOT_FOUND", "지역 정보를 찾을 수 없습니다.")


def chatbot_upstream_error(message: str = "챗봇 응답 생성에 실패했습니다.") -> HTTPException:
    return api_error(502, "CHATBOT_UPSTREAM_ERROR", message)


def client_id_required() -> HTTPException:
    return api_error(400, "CLIENT_ID_REQUIRED", "X-Client-Id 헤더가 필요합니다.")


def invalid_client_id() -> HTTPException:
    return api_error(400, "INVALID_CLIENT_ID", "X-Client-Id가 UUID v4 형식이 아닙니다.")


def image_limit_exceeded() -> HTTPException:
    return api_error(400, "IMAGE_LIMIT_EXCEEDED", "게시글당 이미지는 최대 3장까지 첨부할 수 있습니다.")


def comment_not_found() -> HTTPException:
    return api_error(404, "COMMENT_NOT_FOUND", "댓글을 찾을 수 없습니다.")


def image_not_found() -> HTTPException:
    return api_error(404, "IMAGE_NOT_FOUND", "이미지를 찾을 수 없습니다.")


def image_too_large() -> HTTPException:
    return api_error(413, "IMAGE_TOO_LARGE", "이미지 파일 크기가 허용 범위를 초과했습니다.")


def unsupported_image_type() -> HTTPException:
    return api_error(415, "UNSUPPORTED_IMAGE_TYPE", "허용되지 않는 이미지 형식입니다.")
