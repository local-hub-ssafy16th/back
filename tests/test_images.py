import io

from PIL import Image


def _make_image_bytes(size=(20, 20), fmt="JPEG", color=(255, 0, 0)):
    buf = io.BytesIO()
    Image.new("RGB", size, color=color).save(buf, format=fmt)
    return buf.getvalue()


def _image_file(name="photo.jpg", content_type="image/jpeg", data=None):
    return ("images", (name, data or _make_image_bytes(), content_type))


def _create_post_with_images(client, file_specs, category="tour", password="1234"):
    files = [_image_file(**spec) if isinstance(spec, dict) else spec for spec in file_specs]
    resp = client.post(
        "/api/v2/posts",
        data={"category": category, "title": "이미지 테스트", "content": "본문", "password": password},
        files=files,
    )
    return resp


def test_create_post_with_single_image(client):
    resp = _create_post_with_images(client, [{}])
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert len(body["images"]) == 1
    image = body["images"][0]
    assert image["content_type"] == "image/jpeg"
    assert image["sort_order"] == 0
    assert image["url"] == f"/api/posts/{body['id']}/images/{image['id']}"


def test_image_appears_as_thumbnail_in_list(client):
    resp = _create_post_with_images(client, [{}])
    post = resp.json()

    resp = client.get("/api/v2/posts", params={"category": "tour", "size": 100})
    item = next(i for i in resp.json()["items"] if i["id"] == post["id"])
    assert item["thumbnail_url"] == post["images"][0]["url"]


def test_get_post_image_binary(client):
    post = _create_post_with_images(client, [{}]).json()
    image_id = post["images"][0]["id"]

    resp = client.get(f"/api/posts/{post['id']}/images/{image_id}")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/jpeg"
    assert resp.headers["cache-control"] == "public, max-age=86400"
    assert len(resp.content) > 0


def test_get_post_image_not_found(client):
    post = _create_post_with_images(client, [{}]).json()
    resp = client.get(f"/api/posts/{post['id']}/images/999999")
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "IMAGE_NOT_FOUND"


def test_create_post_image_limit_exceeded(client):
    resp = _create_post_with_images(client, [{}, {}, {}, {}])
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "IMAGE_LIMIT_EXCEEDED"


def test_create_post_unsupported_image_type(client):
    resp = _create_post_with_images(
        client,
        [{"name": "note.txt", "content_type": "text/plain", "data": b"not an image"}],
    )
    assert resp.status_code == 415
    assert resp.json()["detail"]["code"] == "UNSUPPORTED_IMAGE_TYPE"


def test_create_post_image_too_large(client):
    oversized = b"0" * (3 * 1024 * 1024)  # 3MB > 2MB 제한
    resp = _create_post_with_images(
        client, [{"name": "big.jpg", "content_type": "image/jpeg", "data": oversized}]
    )
    assert resp.status_code == 413
    assert resp.json()["detail"]["code"] == "IMAGE_TOO_LARGE"


def test_delete_post_cascades_images(client):
    post = _create_post_with_images(client, [{}]).json()
    image_id = post["images"][0]["id"]

    resp = client.request("DELETE", f"/api/posts/{post['id']}", json={"password": "1234"})
    assert resp.status_code == 204

    resp = client.get(f"/api/posts/{post['id']}/images/{image_id}")
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "POST_NOT_FOUND"


def test_update_post_keep_and_add_images(client):
    post = _create_post_with_images(client, [{}, {}]).json()
    keep_id = post["images"][0]["id"]
    drop_id = post["images"][1]["id"]

    resp = client.put(
        f"/api/v2/posts/{post['id']}",
        data={
            "title": "수정된 제목",
            "content": "수정된 내용",
            "password": "1234",
            "keep_image_ids": str(keep_id),
        },
        files=[_image_file(name="new.jpg")],
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    image_ids = [img["id"] for img in body["images"]]
    assert keep_id in image_ids
    assert drop_id not in image_ids
    assert len(image_ids) == 2

    resp = client.get(f"/api/posts/{post['id']}/images/{drop_id}")
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "IMAGE_NOT_FOUND"


def test_update_post_without_keep_image_ids_clears_existing_images(client):
    post = _create_post_with_images(client, [{}]).json()

    resp = client.put(
        f"/api/v2/posts/{post['id']}",
        data={"title": "제목", "content": "내용", "password": "1234"},
    )
    assert resp.status_code == 200
    assert resp.json()["images"] == []


def test_update_post_keep_image_ids_from_other_post_rejected(client):
    post_a = _create_post_with_images(client, [{}]).json()
    post_b = _create_post_with_images(client, [{}]).json()
    foreign_id = post_a["images"][0]["id"]

    resp = client.put(
        f"/api/v2/posts/{post_b['id']}",
        data={
            "title": "제목",
            "content": "내용",
            "password": "1234",
            "keep_image_ids": str(foreign_id),
        },
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "INVALID_PARAMETER"


def test_update_post_image_limit_exceeded(client):
    post = _create_post_with_images(client, [{}, {}, {}]).json()
    keep_ids = ",".join(str(img["id"]) for img in post["images"])

    resp = client.put(
        f"/api/v2/posts/{post['id']}",
        data={
            "title": "제목",
            "content": "내용",
            "password": "1234",
            "keep_image_ids": keep_ids,
        },
        files=[_image_file(name="extra.jpg")],
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "IMAGE_LIMIT_EXCEEDED"
