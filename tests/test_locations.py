def test_list_locations_default_pagination(client):
    resp = client.get("/api/locations")
    assert resp.status_code == 200
    body = resp.json()
    assert body["page"] == 1
    assert body["size"] == 10
    assert body["total"] == 6518
    assert len(body["items"]) == 10
    titles = [item["title"] for item in body["items"]]
    assert titles == sorted(titles)  # title 오름차순 정렬


def test_list_locations_filter_by_content_type(client):
    resp = client.get("/api/locations", params={"content_type_id": "12"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 783
    assert all(item["content_type_id"] == "12" for item in body["items"])
    assert all(item["content_type_name"] == "관광지" for item in body["items"])


def test_list_locations_invalid_content_type(client):
    resp = client.get("/api/locations", params={"content_type_id": "99"})
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "INVALID_PARAMETER"


def test_list_locations_food_returns_empty_not_error(client):
    resp = client.get("/api/locations", params={"content_type_id": "39"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 0
    assert body["items"] == []


def test_list_locations_filter_by_sigungu(client):
    resp = client.get("/api/locations", params={"sigungu": "110"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 681
    assert all(item["sigungu_name"] == "종로구" for item in body["items"])


def test_list_locations_invalid_sigungu(client):
    resp = client.get("/api/locations", params={"sigungu": "999"})
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "INVALID_PARAMETER"


def test_list_locations_keyword_search(client):
    resp = client.get("/api/locations", params={"keyword": "한강공원"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert all("한강공원" in item["title"] for item in body["items"])


def test_list_locations_page_size_bounds(client):
    resp = client.get("/api/locations", params={"size": 0})
    assert resp.status_code == 422

    resp = client.get("/api/locations", params={"size": 101})
    assert resp.status_code == 422

    resp = client.get("/api/locations", params={"page": 0})
    assert resp.status_code == 422


def test_get_location_detail(client):
    listed = client.get("/api/locations", params={"content_type_id": "15", "size": 1}).json()
    content_id = listed["items"][0]["content_id"]

    resp = client.get(f"/api/locations/{content_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["content_id"] == content_id
    assert body["source"] == {
        "provider": "한국관광공사",
        "dataset": "국문 관광정보 서비스 (TourAPI 4.0)",
        "url": "https://www.data.go.kr/data/15101578/openapi.do",
        "license": "공공누리 제3유형",
    }
    # 축제공연행사 상세에도 일정 필드는 존재하지 않는다
    assert "eventstartdate" not in body
    assert "eventenddate" not in body


def test_get_location_detail_not_found(client):
    resp = client.get("/api/locations/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "LOCATION_NOT_FOUND"


def test_meta_categories(client):
    resp = client.get("/api/locations/meta/categories")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 6518

    by_id = {item["content_type_id"]: item for item in body["items"]}
    assert by_id["12"]["count"] == 783
    assert by_id["12"]["available"] is True
    assert by_id["39"]["count"] == 0
    assert by_id["39"]["available"] is False


def test_meta_sigungu(client):
    resp = client.get("/api/locations/meta/sigungu")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 25
    codes = [item["code"] for item in body["items"]]
    assert codes == sorted(codes, key=int)  # code 오름차순
    # lDongSignguCd 미기재 2건은 25개 자치구 어디에도 집계되지 않는다 (2.5절)
    assert sum(item["count"] for item in body["items"]) == 6516
