def test_create_post(create_post):
    post = create_post(title="양화한강공원 야경 좋네요", content="저녁 8시쯤 추천")
    assert post["category"] == "tour"
    assert post["title"] == "양화한강공원 야경 좋네요"
    assert post["content"] == "저녁 8시쯤 추천"
    assert "password" not in post


def test_create_post_invalid_category(client):
    resp = client.post(
        "/api/posts",
        json={"category": "invalid", "title": "t", "content": "c", "password": "1234"},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "INVALID_PARAMETER"


def test_create_post_validation_error(client):
    resp = client.post(
        "/api/posts",
        json={"category": "tour", "title": "", "content": "c", "password": "1234"},
    )
    assert resp.status_code == 422


def test_list_posts_excludes_content_and_password(client, create_post):
    create_post(title="목록 테스트 게시글")
    resp = client.get("/api/posts")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    item = body["items"][0]
    assert "content" not in item
    assert "password" not in item


def test_list_posts_sorted_by_created_at_desc(client, create_post):
    first = create_post(title="첫 번째 글")
    second = create_post(title="두 번째 글")
    resp = client.get("/api/posts", params={"size": 2})
    ids = [item["id"] for item in resp.json()["items"]]
    assert ids.index(second["id"]) < ids.index(first["id"])


def test_list_posts_filter_by_category(client, create_post):
    create_post(category="food", title="맛집 게시글")
    resp = client.get("/api/posts", params={"category": "food"})
    assert resp.status_code == 200
    assert all(item["category"] == "food" for item in resp.json()["items"])


def test_list_posts_invalid_category(client):
    resp = client.get("/api/posts", params={"category": "invalid"})
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "INVALID_PARAMETER"


def test_get_post_detail_includes_content_not_password(client, create_post):
    post = create_post()
    resp = client.get(f"/api/posts/{post['id']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["content"] == post["content"]
    assert "password" not in body


def test_get_post_not_found(client):
    resp = client.get("/api/posts/999999")
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "POST_NOT_FOUND"


def test_verify_password_success_and_failure(client, create_post):
    post = create_post(password="1234")

    resp = client.post(f"/api/posts/{post['id']}/verify", json={"password": "wrong"})
    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "PASSWORD_MISMATCH"

    resp = client.post(f"/api/posts/{post['id']}/verify", json={"password": "1234"})
    assert resp.status_code == 200
    assert resp.json() == {"verified": True}


def test_verify_password_post_not_found(client):
    resp = client.post("/api/posts/999999/verify", json={"password": "1234"})
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "POST_NOT_FOUND"


def test_update_post(client, create_post):
    post = create_post(password="1234")

    resp = client.put(
        f"/api/posts/{post['id']}",
        json={"title": "수정된 제목", "content": "수정된 내용", "password": "wrong"},
    )
    assert resp.status_code == 403

    resp = client.put(
        f"/api/posts/{post['id']}",
        json={"title": "수정된 제목", "content": "수정된 내용", "password": "1234"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "수정된 제목"
    assert body["content"] == "수정된 내용"
    assert body["updated_at"] >= post["updated_at"]


def test_update_post_not_found(client):
    resp = client.put(
        "/api/posts/999999",
        json={"title": "t", "content": "c", "password": "1234"},
    )
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "POST_NOT_FOUND"


def test_delete_post(client, create_post):
    post = create_post(password="1234")

    resp = client.request("DELETE", f"/api/posts/{post['id']}", json={"password": "wrong"})
    assert resp.status_code == 403

    resp = client.request("DELETE", f"/api/posts/{post['id']}", json={"password": "1234"})
    assert resp.status_code == 204
    assert resp.content == b""

    resp = client.get(f"/api/posts/{post['id']}")
    assert resp.status_code == 404


def test_delete_post_not_found(client):
    resp = client.request("DELETE", "/api/posts/999999", json={"password": "1234"})
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "POST_NOT_FOUND"
