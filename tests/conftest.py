import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
TEST_DB_PATH = BACKEND_DIR / "test_dongne.db"

# app.config.settings 는 import 시점에 생성되므로, app을 import 하기 전에
# 환경변수를 지정해 테스트 전용 DB/데이터 경로를 쓰도록 한다 (개발용 dongne.db 오염 방지).
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["DATA_DIR"] = str(BACKEND_DIR / "data" / "seoul")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-key")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")

import pytest
from fastapi.testclient import TestClient

from app.database import engine
from app.main import app


@pytest.fixture(scope="session")
def client():
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    with TestClient(app) as test_client:
        yield test_client

    # Windows에서는 SQLite 커넥션을 반납하기 전에는 파일 삭제가 실패하므로 먼저 dispose 한다.
    engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture
def create_post(client):
    created_ids = []

    def _create(category="tour", title="테스트 게시글", content="테스트 내용", password="1234"):
        resp = client.post(
            "/api/v2/posts",
            data={"category": category, "title": title, "content": content, "password": password},
        )
        assert resp.status_code == 201, resp.text
        post_id = resp.json()["id"]
        created_ids.append(post_id)
        return resp.json()

    yield _create

    for post_id in created_ids:
        client.request("DELETE", f"/api/posts/{post_id}", json={"password": "1234"})
