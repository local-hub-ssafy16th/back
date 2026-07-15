# 동네방네 API 명세서

공공데이터 기반 지역 정보 공유 커뮤니티 — **서울(SEL) 권역**

| 항목 | 내용 |
|------|------|
| 문서 버전 | v1.0 |
| 작성일 | 2026-07-15 |
| 근거 문서 | 02_3일차_팀프로젝트_개발_의뢰서, 동네방네 기능 명세서, SCHEMA.md, SOURCE.md |
| 대상 권역 | 서울 (SEL) — `lDongRegnCd = "11"` |
| 백엔드 | FastAPI + SQLAlchemy ORM + SQLite |
| 배포 | Render (Backend) / Netlify (Frontend) |

---

## 1. 공통 규약

### 1.1 Base URL

| 환경 | URL |
|------|-----|
| 로컬 | `http://localhost:8000` |
| 운영 | `https://{render-service}.onrender.com` |

모든 엔드포인트는 `/api` 프리픽스를 가진다. API 문서는 FastAPI 자동 생성 `/docs`(Swagger UI)로 검증한다.

### 1.2 공통 헤더

| 구분 | 헤더 | 값 |
|------|------|-----|
| Request | `Content-Type` | `application/json` (Body 있는 요청) |
| Response | `Content-Type` | `application/json; charset=utf-8` |

### 1.3 CORS

Netlify 배포 도메인과 로컬 개발 서버를 허용한다. 허용 오리진은 `.env`의 `CORS_ORIGINS`로 관리한다.

```python
allow_origins = ["http://localhost:5173", "https://{netlify-site}.netlify.app"]
allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
allow_headers = ["*"]
allow_credentials = False   # 인증 체계 미적용(익명 커뮤니티)
```

### 1.4 공통 에러 응답

FastAPI `HTTPException`의 `detail`에 아래 구조를 담는다.

```json
{
  "detail": {
    "code": "PASSWORD_MISMATCH",
    "message": "비밀번호가 일치하지 않습니다."
  }
}
```

| 상태코드 | code | 발생 조건 |
|---------|------|----------|
| 400 | `INVALID_PARAMETER` | 파라미터 값이 허용 범위를 벗어남 (예: 미정의 카테고리) |
| 403 | `PASSWORD_MISMATCH` | 게시글 수정·삭제 시 비밀번호 불일치 |
| 404 | `POST_NOT_FOUND` | 존재하지 않는 게시글 ID |
| 404 | `LOCATION_NOT_FOUND` | 존재하지 않는 `content_id` |
| 422 | (FastAPI 기본) | Pydantic 검증 실패 — 필수 필드 누락, 타입 불일치 |
| 500 | `INTERNAL_ERROR` | 서버 내부 오류 |
| 502 | `CHATBOT_UPSTREAM_ERROR` | OpenAI API 호출 실패·타임아웃 |

> 422는 FastAPI가 자동 생성하는 `RequestValidationError` 형식을 그대로 사용한다.

### 1.5 페이지네이션 공통 응답

목록 조회 API는 모두 아래 래핑 구조를 반환한다.

```json
{
  "items": [ ... ],
  "page": 1,
  "size": 10,
  "total": 783,
  "total_pages": 79
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `items` | array | 조회 결과 배열 |
| `page` | integer | 현재 페이지 (1부터 시작) |
| `size` | integer | 페이지당 항목 수 |
| `total` | integer | 조건에 맞는 전체 항목 수 |
| `total_pages` | integer | 전체 페이지 수 (`ceil(total / size)`) |

공통 쿼리 파라미터:

| 파라미터 | 타입 | 필수 | 기본값 | 제약 |
|---------|------|------|--------|------|
| `page` | integer | N | 1 | ≥ 1 |
| `size` | integer | N | 10 | 1 ~ 100 |

### 1.6 환경변수 (.env)

`.env`는 반드시 `.gitignore`에 등록하며 저장소에 포함하지 않는다. (의뢰서 III-백엔드 나항)

| 변수 | 설명 | 예시 |
|------|------|------|
| `DATABASE_URL` | SQLite 경로 | `sqlite:///./dongne.db` |
| `OPENAI_API_KEY` | 챗봇용 OpenAI API 키 | `sk-...` |
| `OPENAI_MODEL` | 사용 모델명 | `gpt-4o-mini` |
| `CORS_ORIGINS` | 허용 오리진 (콤마 구분) | `https://xxx.netlify.app` |
| `DATA_DIR` | 원본 JSON 디렉토리 | `./data/seoul` |

---

## 2. 데이터 기준

### 2.1 활용 데이터 출처

| 항목 | 내용 |
|------|------|
| 제공 기관 | 한국관광공사 |
| 데이터명 | 국문 관광정보 서비스 (TourAPI 4.0) |
| 원본 URL | https://www.data.go.kr/data/15101578/openapi.do |
| 라이선스 | 공공누리 제3유형 (출처 표시 + 변경 금지) |
| 수집 지역 | 서울 (SEL) |

**변경 금지 조항 준수를 위해 응답 필드명은 TourAPI 원본 필드명을 그대로 유지한다.** (리네이밍·재가공하지 않음)

### 2.2 콘텐츠 유형 및 확보 현황

| contentTypeId | 유형 | 파일 | 건수 | 상태 |
|--------------|------|------|------|------|
| 12 | 관광지 | `서울_관광지.json` | 783 | 확보 |
| 14 | 문화시설 | `서울_문화시설.json` | 566 | 확보 |
| 15 | 축제공연행사 | `서울_축제공연행사.json` | 201 | 확보 |
| 25 | 여행코스 | `서울_여행코스.json` | 51 | 확보 |
| 28 | 레포츠 | `서울_레포츠.json` | 126 | 확보 |
| 32 | 숙박 | `서울_숙박.json` | 423 | 확보 |
| 38 | 쇼핑 | `서울_쇼핑.json` | 4,368 | 확보 |
| 39 | 음식점 | `서울_음식점.json` | — | **데이터 미확보** |

**확보 합계: 6,518건** (전체 8,150건 기준 음식점 1,632건 미확보)

### 2.3 데이터 미확보 항목 — 제약사항

> 아래 두 항목은 본 프로젝트 개발 범위에서 **미구현**으로 처리한다. 추가 수집은 수행하지 않기로 확정하였다.

| 항목 | 내용 | 영향 범위 | 처리 방침 |
|------|------|----------|----------|
| **음식점 데이터 미확보** | `서울_음식점.json`(1,632건) 미제공 | `GET /api/locations` 의 `content_type_id=39` 조회, 홈 화면 '맛집' 카테고리 바로가기, 챗봇의 음식점 추천·모범음식점 위치 질의 | API는 39를 정상 파라미터로 수용하되 `total: 0`, `items: []` 반환. 프론트 홈 화면에서 '맛집' 카드는 비노출. **커뮤니티 게시판의 `food` 카테고리는 지역 정보 데이터와 무관하므로 정상 운영** |
| **축제 일정 필드 부재** | `서울_축제공연행사.json` 201건에 `eventstartdate` / `eventenddate` 필드 없음. 보유 날짜 필드는 `createdtime` / `modifiedtime`(등록·수정 시각)뿐 | 챗봇의 '축제 일정' 질의(의뢰서 III-챗봇 나항 명시 유형) | 챗봇은 일정 질의에 대해 **정보 미보유 응답**을 반환 (기능 명세서 5절 "미보유 정보는 모른다고 응답" 기준 적용). 축제 목록·위치·이미지 조회는 정상 제공 |

### 2.4 필드 사용 정책 — 결측 필드 처리

원본 데이터 실측 결과, 아래 필드는 결측률이 높아 **필터·분류 키로 사용하지 않는다.**

| 필드 | 채워진 비율(유형별) | 판정 |
|------|-------------------|------|
| `areacode` | 쇼핑 3% / 문화시설 47% / 축제 52% / 관광지 58% | **미사용** |
| `sigungucode` | 쇼핑 3% / 문화시설 47% / 축제 52% / 관광지 58% | **미사용** |
| `cat1` `cat2` `cat3` | 쇼핑 3% / 문화시설 47% / 관광지 58% / 숙박 76% | **미사용** |
| `lDongRegnCd` | 100% | 사용 (서울 = `11`) |
| `lDongSignguCd` | 100% (미기재 2건) | **자치구 필터 키로 사용** |
| `lclsSystm1~3` | 100% | 보조 분류로 응답에 포함 |
| `mapx` `mapy` | 100% (빈값 0건) | 사용 (float 변환 후 응답) |

기타 결측 특성:

- `여행코스`(25) 51건은 `addr1` / `zipcode`가 전부 빈 문자열 → 프론트에서 주소 영역 비노출 처리
- `tel`은 축제공연행사(15)만 채워짐 → 그 외 유형은 전화번호 비노출
- `firstimage` 결측: 숙박 55%, 관광지 9%, 레포츠 10% → 이미지 없을 시 플레이스홀더 처리
- 원본이 빈 문자열(`""`)인 필드는 API 응답에서 **`null`로 정규화**한다

### 2.5 서울 자치구 코드 (`lDongSignguCd`)

`GET /api/locations` 의 `sigungu` 파라미터에 사용한다. 데이터 실측 기준 25개 자치구 전부 존재하며, 코드 미기재 2건은 필터 조회 시 제외된다.

| 코드 | 자치구 | 코드 | 자치구 | 코드 | 자치구 |
|------|--------|------|--------|------|--------|
| 110 | 종로구 | 350 | 노원구 | 590 | 동작구 |
| 140 | 중구 | 380 | 은평구 | 620 | 관악구 |
| 170 | 용산구 | 410 | 서대문구 | 650 | 서초구 |
| 200 | 성동구 | 440 | 마포구 | 680 | 강남구 |
| 215 | 광진구 | 470 | 양천구 | 710 | 송파구 |
| 230 | 동대문구 | 500 | 강서구 | 740 | 강동구 |
| 260 | 중랑구 | 530 | 구로구 | | |
| 290 | 성북구 | 545 | 금천구 | | |
| 305 | 강북구 | 560 | 영등포구 | | |
| 320 | 도봉구 | | | | |

### 2.6 커뮤니티 게시판 카테고리

와이어프레임(의뢰서 [참고 4] ①)의 3개 카테고리 바로가기 기준으로 정의한다.

| code | 표시명 | 비고 |
|------|--------|------|
| `tour` | 관광지 | |
| `food` | 맛집 | 지역 정보 데이터 미확보와 무관하게 게시판은 정상 운영 |
| `festival` | 축제·행사 | |

정의되지 않은 값 요청 시 `400 INVALID_PARAMETER`.

---

## 3. DB 스키마

### 3.1 `posts` — 커뮤니티 게시글

```sql
CREATE TABLE posts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    category    VARCHAR(20)  NOT NULL,          -- tour | food | festival
    title       VARCHAR(200) NOT NULL,
    content     TEXT         NOT NULL,
    password    VARCHAR(100) NOT NULL,          -- 평문 저장(의뢰서 III-커뮤니티 나항, 교육 목적 의도된 설계)
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_posts_category   ON posts (category);
CREATE INDEX ix_posts_created_at ON posts (created_at DESC);
```

> `password`는 의뢰서 III-커뮤니티 나항에 따라 **암호화 없이 평문으로 저장·비교**한다. 이는 교육 목적의 의도된 설계이며, 어떤 API 응답에도 노출하지 않는다.

### 3.2 `locations` — 지역 정보 (TourAPI 원본)

서버 기동 시 `DATA_DIR`의 JSON을 읽어 적재한다(멱등, `content_id` 기준 upsert). 검색·페이지네이션 성능 확보를 위해 DB에 적재하며, 원본 필드값은 변형하지 않는다.

```sql
CREATE TABLE locations (
    content_id       VARCHAR(20)  PRIMARY KEY,   -- contentid
    content_type_id  VARCHAR(5)   NOT NULL,      -- contenttypeid
    title            VARCHAR(300) NOT NULL,
    addr1            VARCHAR(300),
    addr2            VARCHAR(300),
    zipcode          VARCHAR(20),
    tel              VARCHAR(100),
    mapx             REAL,                       -- 원본 string → float 변환
    mapy             REAL,
    mlevel           VARCHAR(5),
    l_dong_regn_cd   VARCHAR(5),                 -- lDongRegnCd  (서울 = 11)
    l_dong_signgu_cd VARCHAR(5),                 -- lDongSignguCd (자치구)
    lcls_systm1      VARCHAR(10),
    lcls_systm2      VARCHAR(10),
    lcls_systm3      VARCHAR(20),
    firstimage       VARCHAR(500),
    firstimage2      VARCHAR(500),
    cpyrht_div_cd    VARCHAR(10),
    createdtime      VARCHAR(14),                -- YYYYMMDDHHmmss 원본 유지
    modifiedtime     VARCHAR(14)
);
CREATE INDEX ix_locations_type   ON locations (content_type_id);
CREATE INDEX ix_locations_signgu ON locations (l_dong_signgu_cd);
CREATE INDEX ix_locations_title  ON locations (title);
```

미적재 필드: `areacode`, `sigungucode`, `cat1~3` — 2.4절 결측률 사유로 제외.

---

## 4. API 목록

| # | Method | Endpoint | 설명 | 구분 |
|---|--------|----------|------|------|
| 1 | GET | `/api/health` | 서버 상태 확인 | 공통 |
| 2 | GET | `/api/locations` | 지역 정보 목록 조회 | 지역 정보 |
| 3 | GET | `/api/locations/{content_id}` | 지역 정보 상세 조회 | 지역 정보 |
| 4 | GET | `/api/locations/meta/categories` | 콘텐츠 유형 목록·건수 | 지역 정보 |
| 5 | GET | `/api/locations/meta/sigungu` | 자치구 목록 | 지역 정보 |
| 6 | GET | `/api/posts` | 게시글 목록 조회 (검색·페이징) | 커뮤니티 |
| 7 | GET | `/api/posts/{post_id}` | 게시글 상세 조회 | 커뮤니티 |
| 8 | POST | `/api/posts` | 게시글 작성 | 커뮤니티 |
| 9 | POST | `/api/posts/{post_id}/verify` | 수정용 비밀번호 확인 | 커뮤니티 |
| 10 | PUT | `/api/posts/{post_id}` | 게시글 수정 | 커뮤니티 |
| 11 | DELETE | `/api/posts/{post_id}` | 게시글 삭제 | 커뮤니티 |
| 12 | POST | `/api/chat` | 챗봇 질의응답 | 챗봇 |

---

## 5. 지역 정보 API

### 5.1 `GET /api/locations` — 지역 정보 목록 조회

선정 권역(서울)의 지역 정보를 유형·자치구·키워드로 필터링하여 페이징 조회한다.

**Query Parameters**

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `content_type_id` | string | N | (전체) | 콘텐츠 유형. `12` `14` `15` `25` `28` `32` `38` `39` 중 하나 |
| `sigungu` | string | N | (전체) | 자치구 코드 (`lDongSignguCd`). 2.5절 표 참조 |
| `keyword` | string | N | — | `title` 부분 일치 검색 (LIKE, 대소문자 무시) |
| `page` | integer | N | 1 | ≥ 1 |
| `size` | integer | N | 10 | 1 ~ 100 |

**Response 200**

```json
{
  "items": [
    {
      "content_id": "1059877",
      "content_type_id": "12",
      "content_type_name": "관광지",
      "title": "양화한강공원",
      "addr1": "서울특별시 영등포구 노들로 221 (당산동)",
      "addr2": null,
      "sigungu_name": "영등포구",
      "firstimage": "https://tong.visitkorea.or.kr/cms/resource_photo/46/3551346_image2_1.jpg",
      "firstimage2": "https://tong.visitkorea.or.kr/cms/resource_photo/46/3551346_image3_1.jpg",
      "mapx": 126.902365881,
      "mapy": 37.5382819489
    }
  ],
  "page": 1,
  "size": 10,
  "total": 350,
  "total_pages": 35
}
```

목록 응답은 카드 렌더링에 필요한 필드만 포함한다(경량화). 전체 필드는 상세 조회에서 제공한다.

**정렬**: `title` 오름차순 (가나다순)

**Error**

| 상태코드 | 조건 |
|---------|------|
| 400 `INVALID_PARAMETER` | `content_type_id`가 정의된 8종에 없음 / `sigungu`가 25개 코드에 없음 |
| 422 | `page` < 1, `size` 범위 초과 등 타입·범위 위반 |

> **`content_type_id=39`(음식점) 조회 시**: 데이터 미확보로 `total: 0`, `items: []`를 반환한다. 에러가 아니다.

---

### 5.2 `GET /api/locations/{content_id}` — 지역 정보 상세 조회

**Path Parameters**

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `content_id` | string | TourAPI `contentid` |

**Response 200**

```json
{
  "content_id": "2556687",
  "content_type_id": "15",
  "content_type_name": "축제공연행사",
  "title": "문학주간 2026",
  "addr1": "서울특별시 종로구 대학로 104 (동숭동)",
  "addr2": null,
  "zipcode": "03087",
  "tel": "070-7954-1369",
  "mapx": 127.0023742293,
  "mapy": 37.580512461,
  "mlevel": "6",
  "l_dong_regn_cd": "11",
  "l_dong_signgu_cd": "110",
  "sigungu_name": "종로구",
  "lcls_systm1": "EV",
  "lcls_systm2": "EV03",
  "lcls_systm3": "EV030400",
  "firstimage": "https://tong.visitkorea.or.kr/cms/resource/47/4077947_image2_1.jpg",
  "firstimage2": "https://tong.visitkorea.or.kr/cms/resource/47/4077947_image3_1.jpg",
  "cpyrht_div_cd": "Type3",
  "createdtime": "20180808012040",
  "modifiedtime": "20260622154640",
  "source": {
    "provider": "한국관광공사",
    "dataset": "국문 관광정보 서비스 (TourAPI 4.0)",
    "url": "https://www.data.go.kr/data/15101578/openapi.do",
    "license": "공공누리 제3유형"
  }
}
```

`source` 객체는 공공누리 제3유형의 **출처 표시 의무** 이행을 위해 상세 응답에 포함한다. (SOURCE.md 기준)

> 축제공연행사(15) 상세에도 `eventstartdate` / `eventenddate`는 **제공되지 않는다** (2.3절).

**Error**

| 상태코드 | 조건 |
|---------|------|
| 404 `LOCATION_NOT_FOUND` | 해당 `content_id` 없음 |

---

### 5.3 `GET /api/locations/meta/categories` — 콘텐츠 유형 목록

홈 화면 카테고리 바로가기 및 필터 UI 구성용.

**Response 200**

```json
{
  "items": [
    { "content_type_id": "12", "name": "관광지",       "count": 783,  "available": true },
    { "content_type_id": "14", "name": "문화시설",     "count": 566,  "available": true },
    { "content_type_id": "15", "name": "축제공연행사", "count": 201,  "available": true },
    { "content_type_id": "25", "name": "여행코스",     "count": 51,   "available": true },
    { "content_type_id": "28", "name": "레포츠",       "count": 126,  "available": true },
    { "content_type_id": "32", "name": "숙박",         "count": 423,  "available": true },
    { "content_type_id": "38", "name": "쇼핑",         "count": 4368, "available": true },
    { "content_type_id": "39", "name": "음식점",       "count": 0,    "available": false }
  ],
  "total": 6518
}
```

| 필드 | 설명 |
|------|------|
| `count` | DB 적재 건수 |
| `available` | 데이터 확보 여부. **프론트는 `false`인 항목을 비노출 처리한다** |

---

### 5.4 `GET /api/locations/meta/sigungu` — 자치구 목록

**Response 200**

```json
{
  "items": [
    { "code": "110", "name": "종로구", "count": 681 },
    { "code": "140", "name": "중구",   "count": 787 }
  ],
  "total": 25
}
```

`count`는 해당 자치구의 지역 정보 건수. `code` 오름차순 정렬.

---

## 6. 커뮤니티 API

### 6.1 `GET /api/posts` — 게시글 목록 조회

**Query Parameters**

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `category` | string | N | (전체) | `tour` \| `food` \| `festival` |
| `keyword` | string | N | — | 제목 + 내용 부분 일치 검색 |
| `page` | integer | N | 1 | ≥ 1 |
| `size` | integer | N | 10 | 1 ~ 100 |

**Response 200**

```json
{
  "items": [
    {
      "id": 7,
      "category": "tour",
      "title": "양화한강공원 야경 좋네요",
      "created_at": "2026-07-01T14:03:22",
      "updated_at": "2026-07-01T14:03:22"
    }
  ],
  "page": 1,
  "size": 10,
  "total": 21,
  "total_pages": 3
}
```

목록 응답에 `content`와 `password`는 포함하지 않는다.

**정렬**: `created_at` 내림차순 (최신순) — 와이어프레임의 번호 역순 표기와 일치

**Error**

| 상태코드 | 조건 |
|---------|------|
| 400 `INVALID_PARAMETER` | `category`가 정의된 3종에 없음 |

---

### 6.2 `GET /api/posts/{post_id}` — 게시글 상세 조회

**Response 200**

```json
{
  "id": 7,
  "category": "tour",
  "title": "양화한강공원 야경 좋네요",
  "content": "저녁 8시쯤 가면 사람도 적고 좋습니다.",
  "created_at": "2026-07-01T14:03:22",
  "updated_at": "2026-07-01T14:03:22"
}
```

`password`는 **어떤 경우에도 응답에 포함하지 않는다.**

**Error**

| 상태코드 | 조건 |
|---------|------|
| 404 `POST_NOT_FOUND` | 해당 `post_id` 없음 |

---

### 6.3 `POST /api/posts` — 게시글 작성

**Request Body**

```json
{
  "category": "tour",
  "title": "양화한강공원 야경 좋네요",
  "content": "저녁 8시쯤 가면 사람도 적고 좋습니다.",
  "password": "1234"
}
```

| 필드 | 타입 | 필수 | 제약 |
|------|------|------|------|
| `category` | string | Y | `tour` \| `food` \| `festival` |
| `title` | string | Y | 1 ~ 200자, 공백만 입력 불가 |
| `content` | string | Y | 1 ~ 5000자, 공백만 입력 불가 |
| `password` | string | Y | 4 ~ 20자 |

**Response 201**

```json
{
  "id": 8,
  "category": "tour",
  "title": "양화한강공원 야경 좋네요",
  "content": "저녁 8시쯤 가면 사람도 적고 좋습니다.",
  "created_at": "2026-07-15T10:22:01",
  "updated_at": "2026-07-15T10:22:01"
}
```

**Error**

| 상태코드 | 조건 |
|---------|------|
| 400 `INVALID_PARAMETER` | `category` 미정의 값 |
| 422 | 필수 필드 누락, 길이 제약 위반 |

---

### 6.4 `POST /api/posts/{post_id}/verify` — 수정용 비밀번호 확인

와이어프레임 ③(게시글 상세)의 **비밀번호 확인 모달**에 대응한다. 수정·삭제 버튼 클릭 시 이 API로 먼저 검증한 뒤 수정 화면으로 이동하거나 삭제를 실행한다.

**Request Body**

```json
{ "password": "1234" }
```

**Response 200**

```json
{ "verified": true }
```

> **본 API는 UX 목적의 사전 확인이며 세션·토큰을 발급하지 않는다.** 서버는 무상태(stateless)로 동작하므로, `PUT` / `DELETE` 요청 시에도 `password`를 반드시 다시 전송해야 한다. 최종 권한 판정은 `PUT` / `DELETE` 시점에 이루어진다. (의뢰서 III-커뮤니티 가항 — 인증·권한 체계 미적용)

**Error**

| 상태코드 | 조건 |
|---------|------|
| 403 `PASSWORD_MISMATCH` | 비밀번호 불일치 |
| 404 `POST_NOT_FOUND` | 해당 `post_id` 없음 |

> 불일치 시 `{"verified": false}` + 200이 아니라 **403**을 반환한다. 프론트는 403 수신 시 모달에 오류 메시지를 표시한다.

---

### 6.5 `PUT /api/posts/{post_id}` — 게시글 수정

**Request Body**

```json
{
  "title": "양화한강공원 야경 좋네요 (수정)",
  "content": "저녁 8시 이후 추천합니다.",
  "password": "1234"
}
```

| 필드 | 타입 | 필수 | 제약 |
|------|------|------|------|
| `title` | string | Y | 1 ~ 200자 |
| `content` | string | Y | 1 ~ 5000자 |
| `password` | string | Y | 등록된 비밀번호와 평문 비교 |

`category`는 수정 대상에서 제외한다. `password` 변경도 제공하지 않는다.

**처리 순서**

1. `post_id` 존재 확인 → 없으면 404
2. `password` 일치 확인 → 불일치 시 403
3. `title`, `content` 갱신 및 `updated_at` = 현재 시각

**Response 200** — 6.2와 동일한 게시글 상세 객체

**Error**

| 상태코드 | 조건 |
|---------|------|
| 403 `PASSWORD_MISMATCH` | 비밀번호 불일치 |
| 404 `POST_NOT_FOUND` | 해당 `post_id` 없음 |
| 422 | 길이 제약 위반 |

---

### 6.6 `DELETE /api/posts/{post_id}` — 게시글 삭제

**Request Body**

```json
{ "password": "1234" }
```

> DELETE에 Body를 사용한다. FastAPI는 `Body` 파라미터로 정상 지원하며, `axios.delete(url, { data: { password } })` 형태로 호출한다.

**처리 순서**

1. `post_id` 존재 확인 → 없으면 404
2. `password` 일치 확인 → 불일치 시 403
3. 레코드 물리 삭제 (Hard delete)

**Response 204** — No Content (응답 Body 없음)

**Error**

| 상태코드 | 조건 |
|---------|------|
| 403 `PASSWORD_MISMATCH` | 비밀번호 불일치 |
| 404 `POST_NOT_FOUND` | 해당 `post_id` 없음 |

---

## 7. 챗봇 API

### 7.1 `POST /api/chat` — 챗봇 질의응답

의뢰서 III-챗봇 가항. 제공 JSON 데이터 기반 자연어 지역 정보 질의응답을 처리한다.

**Request Body**

```json
{
  "message": "종로구 관광지 추천해줘",
  "history": [
    { "role": "user",      "content": "안녕" },
    { "role": "assistant", "content": "안녕하세요! 궁금한 지역 정보를 물어보세요." }
  ]
}
```

| 필드 | 타입 | 필수 | 제약 |
|------|------|------|------|
| `message` | string | Y | 1 ~ 500자 |
| `history` | array | N | 이전 대화. 최근 **10턴**까지만 반영, 초과분은 서버가 절삭 |
| `history[].role` | string | Y | `user` \| `assistant` |
| `history[].content` | string | Y | 1 ~ 2000자 |

> 대화 히스토리는 서버에 저장하지 않는다(무상태). 프론트가 보유·전송한다.

**Response 200**

```json
{
  "reply": "종로구에는 창덕궁, 북촌한옥마을 등이 있습니다. 아래 장소를 확인해보세요.",
  "references": [
    {
      "content_id": "126508",
      "content_type_id": "12",
      "title": "창덕궁",
      "addr1": "서울특별시 종로구 율곡로 99"
    }
  ],
  "post_references": [
    { "id": 7, "category": "tour", "title": "양화한강공원 야경 좋네요" }
  ]
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `reply` | string | 챗봇 응답 텍스트 |
| `references` | array | 응답 근거가 된 지역 정보 (없으면 `[]`). 프론트에서 상세 링크로 연결 |
| `post_references` | array | 관련 커뮤니티 게시글 (없으면 `[]`) |

**처리 흐름**

1. `message`에서 키워드·자치구·콘텐츠 유형 추출
2. `locations` 테이블 검색 → 상위 N건 컨텍스트 구성
3. 게시글 검색 질의로 판단되면 `posts` 테이블도 검색
4. 컨텍스트 + `history`를 OpenAI API에 전달하여 응답 생성
5. `reply` + 근거 데이터 반환

**지원 질의 유형** (의뢰서 III-챗봇 나항)

| 질의 유형 | 지원 | 비고 |
|----------|------|------|
| 관광지 추천 | O | 783건 기반 |
| 축제 **목록·위치** | O | 201건 기반 |
| **축제 일정(날짜)** | **X** | **데이터 미확보 — 정보 미보유 응답 반환** (2.3절) |
| 음식점·모범음식점 위치 | **X** | **데이터 미확보 — 정보 미보유 응답 반환** (2.3절) |
| 커뮤니티 게시글 검색 | O | `posts` 검색 후 `post_references` 반환 |
| 문화시설·숙박·쇼핑·레포츠·여행코스 안내 | O | |

**미보유 정보 응답 규정**

보유하지 않은 정보에 대해서는 **추측하지 않고 미보유임을 명시한다.** (기능 명세서 5절 완료 기준)

| 질의 예시 | 응답 예시 |
|----------|----------|
| "다음 주 축제 일정 알려줘" | "죄송합니다. 현재 축제의 시작·종료 날짜 정보는 보유하고 있지 않습니다. 대신 서울에서 열리는 축제·공연행사 목록과 위치는 안내해드릴 수 있습니다." |
| "강남 맛집 추천해줘" | "죄송합니다. 현재 음식점 데이터는 제공되지 않습니다. 관광지·문화시설·축제 정보는 안내해드릴 수 있습니다." |

시스템 프롬프트에 위 두 항목의 미보유 사실을 명시하여 환각(hallucination)을 방지한다.

**Error**

| 상태코드 | 조건 |
|---------|------|
| 422 | `message` 누락 또는 길이 제약 위반 |
| 502 `CHATBOT_UPSTREAM_ERROR` | OpenAI API 호출 실패·타임아웃 (타임아웃 30초) |

---

## 8. 공통 API

### 8.1 `GET /api/health` — 서버 상태 확인

Render 배포 서비스의 동작 확인용. (의뢰서 III-배포 다항)

**Response 200**

```json
{
  "status": "ok",
  "region": "서울",
  "locations_loaded": 6518
}
```

---

## 9. Pydantic 스키마 정의

```python
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field

Category = Literal["tour", "food", "festival"]

# ---------- 공통 ----------
class ErrorDetail(BaseModel):
    code: str
    message: str

class Page(BaseModel):
    page: int
    size: int
    total: int
    total_pages: int

# ---------- posts ----------
class PostBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=5000)

class PostCreate(PostBase):
    category: Category
    password: str = Field(min_length=4, max_length=20)

class PostUpdate(PostBase):
    password: str = Field(min_length=4, max_length=20)

class PostDelete(BaseModel):
    password: str = Field(min_length=4, max_length=20)

class PasswordVerify(BaseModel):
    password: str = Field(min_length=4, max_length=20)

class PostListItem(BaseModel):
    id: int
    category: Category
    title: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}

class PostDetail(PostListItem):
    content: str            # password 미포함

class PostListResponse(Page):
    items: list[PostListItem]

# ---------- locations ----------
class LocationListItem(BaseModel):
    content_id: str
    content_type_id: str
    content_type_name: str
    title: str
    addr1: Optional[str] = None
    addr2: Optional[str] = None
    sigungu_name: Optional[str] = None
    firstimage: Optional[str] = None
    firstimage2: Optional[str] = None
    mapx: Optional[float] = None
    mapy: Optional[float] = None

class DataSource(BaseModel):
    provider: str = "한국관광공사"
    dataset: str = "국문 관광정보 서비스 (TourAPI 4.0)"
    url: str = "https://www.data.go.kr/data/15101578/openapi.do"
    license: str = "공공누리 제3유형"

class LocationDetail(LocationListItem):
    zipcode: Optional[str] = None
    tel: Optional[str] = None
    mlevel: Optional[str] = None
    l_dong_regn_cd: Optional[str] = None
    l_dong_signgu_cd: Optional[str] = None
    lcls_systm1: Optional[str] = None
    lcls_systm2: Optional[str] = None
    lcls_systm3: Optional[str] = None
    cpyrht_div_cd: Optional[str] = None
    createdtime: Optional[str] = None
    modifiedtime: Optional[str] = None
    source: DataSource = DataSource()

class LocationListResponse(Page):
    items: list[LocationListItem]

# ---------- chat ----------
class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    history: list[ChatMessage] = []

class LocationRef(BaseModel):
    content_id: str
    content_type_id: str
    title: str
    addr1: Optional[str] = None

class PostRef(BaseModel):
    id: int
    category: Category
    title: str

class ChatResponse(BaseModel):
    reply: str
    references: list[LocationRef] = []
    post_references: list[PostRef] = []
```

---

## 10. 화면 ↔ API 매핑

의뢰서 [참고 4] 화면 구성(안) 기준.

| 화면 | 사용 API |
|------|---------|
| ① 홈 (메인) | `GET /api/locations/meta/categories` (카테고리 바로가기, `available=false` 비노출)<br>`GET /api/posts?size=4` (최근 게시글) |
| ② 게시판 목록 | `GET /api/posts?category=&keyword=&page=&size=10` |
| ③ 게시글 상세 | `GET /api/posts/{id}`<br>`POST /api/posts/{id}/verify` (수정·삭제 클릭 시 모달)<br>`DELETE /api/posts/{id}` |
| ④ 게시글 작성 | `POST /api/posts` |
| ④ 게시글 수정 | `GET /api/posts/{id}` → `PUT /api/posts/{id}` |
| ⑤ 챗봇 위젯 | `POST /api/chat` |
| 지역 정보 목록·상세 | `GET /api/locations`, `GET /api/locations/{content_id}`, `GET /api/locations/meta/sigungu` |

---

## 11. 미결·확인 필요 사항

| # | 항목 | 내용 |
|---|------|------|
| 1 | 음식점 데이터 | 의뢰서 [참고 3]·기능 명세서 3.3절에 서울 8개 파일(음식점 1,632건 포함)이 명시되어 있으나 미제공. 고객사 확인 필요. 미확보 상태로 개발 진행 확정 |
| 2 | 축제 일정 필드 | 의뢰서 III-챗봇 나항의 '축제 일정' 질의 유형은 데이터 부재로 미충족. 정보 미보유 응답으로 처리 확정 |
| 3 | `lclsSystemCode.json` | `lclsSystm1~3` 코드→한글명 매핑 테이블 미제공. 응답에 코드만 포함하며 화면 표기는 하지 않음 |
| 4 | Render 콜드 스타트 | 무료 플랜 사용 시 첫 요청 지연(최대 50초) 발생 가능. 시연 전 워밍업 필요 |
