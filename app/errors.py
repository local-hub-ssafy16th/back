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
