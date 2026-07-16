from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import schemas
from .config import settings
from .data_loader import load_locations
from .database import Base, SessionLocal, engine
from .errors import api_error
from .models import Location
from .routers import chat, comments, locations, posts
from .seed_posts import seed_initial_posts


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        load_locations(db)
        seed_initial_posts(db)
    finally:
        db.close()
    yield


app = FastAPI(title="동네방네 API", version="1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Client-Id"],
    allow_credentials=False,
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=api_error(500, "INTERNAL_ERROR", "서버 내부 오류가 발생했습니다.").detail,
    )


api_router_prefix = "/api"
app.include_router(locations.router, prefix=api_router_prefix)
app.include_router(posts.posts_router, prefix=api_router_prefix)
app.include_router(posts.posts_v2_router, prefix=api_router_prefix)
app.include_router(comments.post_comments_router, prefix=api_router_prefix)
app.include_router(comments.comments_router, prefix=api_router_prefix)
app.include_router(chat.router, prefix=api_router_prefix)


@app.get(f"{api_router_prefix}/health", response_model=schemas.HealthResponse)
def health():
    db = SessionLocal()
    try:
        locations_loaded = db.query(Location).count()
    finally:
        db.close()
    return schemas.HealthResponse(status="ok", region="서울", locations_loaded=locations_loaded)
