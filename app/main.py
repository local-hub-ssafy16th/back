from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine
from . import models, schemas, chatbot

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FastAPI SQLite Starter")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"message": "FastAPI + SQLite 기본 세팅 완료"}


@app.get("/items")
def read_items(db: Session = Depends(get_db)):
    return db.query(models.Item).all()


@app.post("/api/chat", response_model=schemas.ChatResponse)
async def chat_endpoint(request: schemas.ChatRequest, db: Session = Depends(get_db)):
    return await chatbot.get_chatbot_reply(db, request.message, request.history)
