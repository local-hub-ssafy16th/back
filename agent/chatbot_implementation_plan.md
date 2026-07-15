# 챗봇 API (POST /api/chat) 구현을 위한 TO-DO LIST

본 문서는 [동네방네_API_명세서.md](file:///C:/Users/SSAFY/back/동네방네_API_명세서.md) 파일의 명세를 바탕으로, FastAPI 백엔드에 챗봇 API를 추가하고 기능을 구현하기 위한 전체 로직 및 단계별 TO-DO LIST를 기술합니다.

---

## 🤖 챗봇 API 핵심 요구사항 및 제약사항

1. **컨텍스트 기반 자연어 검색**:
   - 사용자의 입력(`message`)에서 **자치구**(예: 종로구, 강남구), **콘텐츠 유형**(관광지, 축제 등), **핵심 키워드**를 추출합니다.
   - 추출한 정보를 기반으로 데이터베이스(`locations`, `posts`)를 조회하여 대화 컨텍스트로 LLM에 제공합니다.
2. **OpenAI API 연동**:
   - `OPENAI_API_KEY`, `OPENAI_MODEL` 환경변수를 설정하고 `gpt-4o-mini` 등의 모델을 사용하여 대화를 생성합니다.
   - 대화 히스토리(`history`)는 최대 **10턴**까지만 유지하여 전송합니다.
3. **결측 데이터에 대한 예외 처리 (환각 방지)**:
   - **음식점 데이터 미확보**: 음식점 추천 시 "음식점 데이터 미제공" 사실을 알리고 다른 유형을 추천하도록 프롬프트에 명시합니다.
   - **축제 일정 필드 부재**: 축제 일정(날짜)을 물어보면 임의로 생성하지 않고 "정보 미보유"를 명시하도록 프롬프트에 설정합니다.
4. **출처 표시 및 참조 연동**:
   - 답변의 근거가 된 관광 정보(`references`) 및 커뮤니티 게시글 정보(`post_references`)를 최종 JSON 응답에 포함해야 합니다.

---

## 📝 단계별 TO-DO LIST

### Phase 1: 개발 환경 및 라이브러리 세팅
- [x] **OpenAI 패키지 추가 및 설치**
  - `requirements.txt`에 `openai` 라이브러리를 추가하고 가상환경(`.venv`)에 패키지를 설치합니다.
- [x] **환경변수(`.env`) 설정**
  - 프로젝트 루트 경로에 `.env` 파일을 생성하고 다음 값을 추가합니다:
    ```env
    OPENAI_API_KEY=your_openai_api_key_here
    OPENAI_MODEL=gpt-4o-mini
    DATABASE_URL=sqlite:///./app.db
    ```
- [x] **설정 로드 모듈 구현**
  - `app/config.py` 또는 `app/main.py`에 환경변수를 로드하는 설정 클래스(pydantic-settings 등 이용)를 구성합니다.

### Phase 2: DB 모델 및 Pydantic 스키마 정의
- [x] **SQLAlchemy 모델 확장 (`app/models.py`)**
  - 명세서의 3.1절 및 3.2절에 맞춰 `posts` 및 `locations` 테이블에 대응하는 SQLAlchemy 모델을 추가 정의합니다.
- [x] **Pydantic 스키마 정의 (`app/schemas.py` 신설)**
  - 명세서 9절에 맞춰 Pydantic 모델을 정의합니다.
    - `ChatMessage`, `ChatRequest`, `LocationRef`, `PostRef`, `ChatResponse`

### Phase 3: 키워드 분석 및 DB 컨텍스트 추출 로직 개발
- [x] **입력 텍스트 형태소/키워드 매핑 유틸 구현**
  - 사용자 질문(`message`)에서 자치구명(예: `종로구`, `중구` 등 25개 자치구) 및 콘텐츠 유형(예: `관광지`, `축제`, `숙박` 등)을 추출하는 단순 매핑 함수를 작성합니다.
- [x] **컨텍스트 조회 및 필터링 쿼리 작성**
  - 분석된 자치구/콘텐츠 유형/검색어를 바탕으로 `locations` 및 `posts` 테이블에서 최적의 추천 후보군(각각 상위 5건 내외)을 검색하는 쿼리를 작성합니다.

### Phase 4: OpenAI API 호출 및 프롬프트 엔지니어링
- [x] **시스템 프롬프트 (System Prompt) 설계**
  - 챗봇의 역할(서울 지역 정보 가이드)을 규정합니다.
  - **제약사항 주입**: "음식점 정보는 수집되지 않아 제공 불가능함", "축제 일정(날짜) 정보는 보유하고 있지 않아 모른다고 답변해야 함"을 명확히 명시합니다.
  - LLM에게 답변 생성 시, 본문에 언급한 장소의 `content_id` 또는 `post_id`를 구조화된 형태로 힌트를 남기게 하거나, 검색된 컨텍스트 목록과 매칭하여 `references` 배열을 추출할 수 있도록 가이드를 줍니다.
- [x] **OpenAI API 연동 함수 작성**
  - `openai` 라이브러리를 사용하여 AsyncOpenAI 클라이언트를 정의하고, 대화 히스토리(`history`)가 10턴을 넘지 않도록 슬라이싱하여 API를 호출합니다.
  - 예외 처리 로직을 추가하여 OpenAI API 호출 실패 시 `502 CHATBOT_UPSTREAM_ERROR`를 반환하도록 설계합니다.

### Phase 5: API 엔드포인트 구현 및 테스트
- [x] **FastAPI 라우터 설정 (`POST /api/chat`)**
  - [app/main.py](file:///C:/Users/SSAFY/back/app/main.py)에 `POST /api/chat` 엔드포인트를 구현합니다.
  - 프론트엔드가 요구하는 `ChatResponse` 규격에 맞춰 JSON을 반환하는지 확인합니다.
- [x] **통합 테스트 수행**
  - Swagger UI(`/docs`)를 통해 시나리오별 테스트를 진행합니다.
    1. **정상 시나리오**: *"종로구 관광지 추천해줘"* -> 관련 관광지 정보와 함께 자연스러운 답변 및 `references` 채워짐 확인.
    2. **데이터 미보유 시나리오 (음식점)**: *"강남구 맛집 알려줘"* -> 정보가 제공되지 않는다는 안내 메시지 반환 확인.
    3. **데이터 미보유 시나리오 (일정)**: *"이번 달 축제 언제 시작해?"* -> 날짜 정보는 보유하고 있지 않다는 답변 반환 확인.
    4. **커뮤니티 검색 시나리오**: *"한강공원 다녀온 사람들 글 있니?"* -> 관련 게시글이 `post_references`에 포함되는지 확인.
