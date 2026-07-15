from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import schemas
from ..chatbot import ChatbotUpstreamError, ask_chatbot, search_locations, search_posts
from ..constants import SIGUNGU_NAMES
from ..deps import get_db
from ..errors import chatbot_upstream_error

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=schemas.ChatResponse)
def chat(body: schemas.ChatRequest, db: Session = Depends(get_db)):
    locations = search_locations(db, body.message, SIGUNGU_NAMES)
    posts = search_posts(db, body.message)

    try:
        reply = ask_chatbot(body.message, body.history, locations, posts)
    except ChatbotUpstreamError as exc:
        raise chatbot_upstream_error(str(exc))

    return schemas.ChatResponse(
        reply=reply,
        references=[
            schemas.LocationRef(
                content_id=loc.content_id,
                content_type_id=loc.content_type_id,
                title=loc.title,
                addr1=loc.addr1,
            )
            for loc in locations
        ],
        post_references=[
            schemas.PostRef(id=post.id, category=post.category, title=post.title)
            for post in posts
        ],
    )
