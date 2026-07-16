CLIENT_ID = "22222222-2222-4222-8222-222222222222"


def test_like_post_success(client, create_post):
    post = create_post()
    resp = client.post(f"/api/posts/{post['id']}/like", headers={"X-Client-Id": CLIENT_ID})
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"post_id": post["id"], "like_count": 1, "liked": True}


def test_like_post_idempotent(client, create_post):
    post = create_post()
    client.post(f"/api/posts/{post['id']}/like", headers={"X-Client-Id": CLIENT_ID})
    resp = client.post(f"/api/posts/{post['id']}/like", headers={"X-Client-Id": CLIENT_ID})
    assert resp.status_code == 200
    assert resp.json()["like_count"] == 1


def test_unlike_post(client, create_post):
    post = create_post()
    client.post(f"/api/posts/{post['id']}/like", headers={"X-Client-Id": CLIENT_ID})

    resp = client.request(
        "DELETE", f"/api/posts/{post['id']}/like", headers={"X-Client-Id": CLIENT_ID}
    )
    assert resp.status_code == 200
    assert resp.json() == {"post_id": post["id"], "like_count": 0, "liked": False}


def test_unlike_post_idempotent(client, create_post):
    post = create_post()
    resp = client.request(
        "DELETE", f"/api/posts/{post['id']}/like", headers={"X-Client-Id": CLIENT_ID}
    )
    assert resp.status_code == 200
    assert resp.json()["like_count"] == 0


def test_like_post_missing_client_id(client, create_post):
    post = create_post()
    resp = client.post(f"/api/posts/{post['id']}/like")
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "CLIENT_ID_REQUIRED"


def test_like_post_invalid_client_id(client, create_post):
    post = create_post()
    resp = client.post(f"/api/posts/{post['id']}/like", headers={"X-Client-Id": "bad-id"})
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "INVALID_CLIENT_ID"


def test_like_post_not_found(client):
    resp = client.post("/api/posts/999999/like", headers={"X-Client-Id": CLIENT_ID})
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "POST_NOT_FOUND"


def test_liked_flag_reflected_in_post_detail(client, create_post):
    post = create_post()
    client.post(f"/api/posts/{post['id']}/like", headers={"X-Client-Id": CLIENT_ID})

    resp = client.get(f"/api/v2/posts/{post['id']}", headers={"X-Client-Id": CLIENT_ID})
    assert resp.json()["liked"] is True
    assert resp.json()["like_count"] == 1

    resp = client.get(f"/api/v2/posts/{post['id']}")
    assert resp.json()["liked"] is False
