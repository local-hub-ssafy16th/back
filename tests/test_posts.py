def test_create_post(create_post):
    post = create_post(title="양화한강공원 야경 좋네요", content="저녁 8시쯤 추천")
    assert post["category"] == "tour"
    assert post["title"] == "양화한강공원 야경 좋네요"
    assert post["content"] == "저녁 8시쯤 추천"
    assert post["view_count"] == 0
    assert post["like_count"] == 0
    assert post["comment_count"] == 0
    assert post["liked"] is False
    assert post["images"] == []
    assert "password" not in post


def test_create_post_invalid_category(client):
    resp = client.post(
        "/api/v2/posts",
        data={"category": "invalid", "title": "t", "content": "c", "password": "1234"},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "INVALID_PARAMETER"


def test_create_post_validation_error(client):
    resp = client.post(
        "/api/v2/posts",
        data={"category": "tour", "title": "", "content": "c", "password": "1234"},
    )
    assert resp.status_code == 422


def test_list_posts_excludes_content_and_password(client, create_post):
    create_post(title="목록 테스트 게시글")
    resp = client.get("/api/v2/posts")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    item = body["items"][0]
    assert "content" not in item
    assert "password" not in item


def test_list_posts_includes_v2_fields(client, create_post):
    create_post(title="v2 필드 확인용 게시글")
    resp = client.get("/api/v2/posts")
    assert resp.status_code == 200
    item = resp.json()["items"][0]
    assert "view_count" in item
    assert "like_count" in item
    assert "comment_count" in item
    assert "thumbnail_url" in item
    assert item["thumbnail_url"] is None


def test_list_posts_sorted_by_created_at_desc(client, create_post):
    first = create_post(title="첫 번째 글")
    second = create_post(title="두 번째 글")
    resp = client.get("/api/v2/posts", params={"size": 2})
    ids = [item["id"] for item in resp.json()["items"]]
    assert ids.index(second["id"]) < ids.index(first["id"])


def test_list_posts_filter_by_category(client, create_post):
    create_post(category="food", title="맛집 게시글")
    resp = client.get("/api/v2/posts", params={"category": "food"})
    assert resp.status_code == 200
    assert all(item["category"] == "food" for item in resp.json()["items"])


def test_list_posts_invalid_category(client):
    resp = client.get("/api/v2/posts", params={"category": "invalid"})
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "INVALID_PARAMETER"


def test_list_posts_invalid_search_scope(client):
    resp = client.get("/api/v2/posts", params={"search_scope": "invalid"})
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "INVALID_PARAMETER"


def test_list_posts_invalid_sort(client):
    resp = client.get("/api/v2/posts", params={"sort": "invalid"})
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "INVALID_PARAMETER"


def test_list_posts_search_scope_title_only(client, create_post):
    create_post(title="검색범위테스트고유제목", content="본문에는 없는 단어")
    resp = client.get(
        "/api/v2/posts", params={"keyword": "검색범위테스트고유제목", "search_scope": "content"}
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 0

    resp = client.get(
        "/api/v2/posts", params={"keyword": "검색범위테스트고유제목", "search_scope": "title"}
    )
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


def test_get_post_detail_includes_content_not_password(client, create_post):
    post = create_post()
    resp = client.get(f"/api/v2/posts/{post['id']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["content"] == post["content"]
    assert "password" not in body


def test_get_post_detail_increments_view_count_once_per_client(client, create_post):
    post = create_post()
    client_id = "11111111-1111-4111-8111-111111111111"

    resp = client.get(f"/api/v2/posts/{post['id']}", headers={"X-Client-Id": client_id})
    assert resp.json()["view_count"] == 1

    resp = client.get(f"/api/v2/posts/{post['id']}", headers={"X-Client-Id": client_id})
    assert resp.json()["view_count"] == 1


def test_get_post_detail_invalid_client_id(client, create_post):
    post = create_post()
    resp = client.get(f"/api/v2/posts/{post['id']}", headers={"X-Client-Id": "not-a-uuid"})
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "INVALID_CLIENT_ID"


def test_get_post_not_found(client):
    resp = client.get("/api/v2/posts/999999")
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
        f"/api/v2/posts/{post['id']}",
        data={"title": "수정된 제목", "content": "수정된 내용", "password": "wrong"},
    )
    assert resp.status_code == 403

    resp = client.put(
        f"/api/v2/posts/{post['id']}",
        data={"title": "수정된 제목", "content": "수정된 내용", "password": "1234"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "수정된 제목"
    assert body["content"] == "수정된 내용"
    assert body["updated_at"] >= post["updated_at"]


def test_update_post_not_found(client):
    resp = client.put(
        "/api/v2/posts/999999",
        data={"title": "t", "content": "c", "password": "1234"},
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

    resp = client.get(f"/api/v2/posts/{post['id']}")
    assert resp.status_code == 404


def test_delete_post_not_found(client):
    resp = client.request("DELETE", "/api/posts/999999", json={"password": "1234"})
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "POST_NOT_FOUND"
