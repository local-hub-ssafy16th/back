def _create_comment(client, post_id, content="저도 어제 다녀왔어요!", password="1234"):
    resp = client.post(
        f"/api/posts/{post_id}/comments", json={"content": content, "password": password}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_create_comment(client, create_post):
    post = create_post()
    comment = _create_comment(client, post["id"])
    assert comment["post_id"] == post["id"]
    assert comment["content"] == "저도 어제 다녀왔어요!"
    assert "password" not in comment


def test_create_comment_post_not_found(client):
    resp = client.post("/api/posts/999999/comments", json={"content": "c", "password": "1234"})
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "POST_NOT_FOUND"


def test_create_comment_validation_error(client, create_post):
    post = create_post()
    resp = client.post(f"/api/posts/{post['id']}/comments", json={"content": "", "password": "1234"})
    assert resp.status_code == 422


def test_comment_count_increments_on_post(client, create_post):
    post = create_post()
    _create_comment(client, post["id"])

    resp = client.get(f"/api/v2/posts/{post['id']}")
    assert resp.json()["comment_count"] == 1


def test_list_comments_ordered_ascending(client, create_post):
    post = create_post()
    first = _create_comment(client, post["id"], content="첫 댓글")
    second = _create_comment(client, post["id"], content="두번째 댓글")

    resp = client.get(f"/api/posts/{post['id']}/comments")
    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()["items"]]
    assert ids.index(first["id"]) < ids.index(second["id"])


def test_list_comments_post_not_found(client):
    resp = client.get("/api/posts/999999/comments")
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "POST_NOT_FOUND"


def test_verify_comment_password_success_and_failure(client, create_post):
    post = create_post()
    comment = _create_comment(client, post["id"], password="1234")

    resp = client.post(f"/api/comments/{comment['id']}/verify", json={"password": "wrong"})
    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "PASSWORD_MISMATCH"

    resp = client.post(f"/api/comments/{comment['id']}/verify", json={"password": "1234"})
    assert resp.status_code == 200
    assert resp.json() == {"verified": True}


def test_verify_comment_not_found(client):
    resp = client.post("/api/comments/999999/verify", json={"password": "1234"})
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "COMMENT_NOT_FOUND"


def test_update_comment(client, create_post):
    post = create_post()
    comment = _create_comment(client, post["id"], password="1234")

    resp = client.put(
        f"/api/comments/{comment['id']}",
        json={"content": "수정된 댓글", "password": "wrong"},
    )
    assert resp.status_code == 403

    resp = client.put(
        f"/api/comments/{comment['id']}",
        json={"content": "수정된 댓글", "password": "1234"},
    )
    assert resp.status_code == 200
    assert resp.json()["content"] == "수정된 댓글"


def test_update_comment_not_found(client):
    resp = client.put(
        "/api/comments/999999", json={"content": "c", "password": "1234"}
    )
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "COMMENT_NOT_FOUND"


def test_delete_comment_decrements_count(client, create_post):
    post = create_post()
    comment = _create_comment(client, post["id"], password="1234")

    resp = client.request(
        "DELETE", f"/api/comments/{comment['id']}", json={"password": "wrong"}
    )
    assert resp.status_code == 403

    resp = client.request(
        "DELETE", f"/api/comments/{comment['id']}", json={"password": "1234"}
    )
    assert resp.status_code == 204

    resp = client.get(f"/api/v2/posts/{post['id']}")
    assert resp.json()["comment_count"] == 0


def test_delete_comment_not_found(client):
    resp = client.request("DELETE", "/api/comments/999999", json={"password": "1234"})
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "COMMENT_NOT_FOUND"


def test_comment_cascade_deleted_with_post(client, create_post):
    post = create_post(password="1234")
    comment = _create_comment(client, post["id"], password="1234")

    resp = client.request("DELETE", f"/api/posts/{post['id']}", json={"password": "1234"})
    assert resp.status_code == 204

    resp = client.post(f"/api/comments/{comment['id']}/verify", json={"password": "1234"})
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "COMMENT_NOT_FOUND"
