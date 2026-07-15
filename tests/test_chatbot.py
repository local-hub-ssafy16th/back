import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture
def mock_openai_chat():
    with patch("openai.resources.chat.completions.AsyncCompletions.create", new_callable=AsyncMock) as mock_create:
        # Mocking OpenAI ChatCompletion response
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "종로구에는 아름다운 경복궁이 있습니다. 방문해보시는 것을 추천합니다."
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_create.return_value = mock_response
        yield mock_create

def test_chat_success(mock_openai_chat):
    """
    정상적인 챗봇 질의응답 API 테스트
    """
    request_data = {
        "message": "종로구 관광지 추천해줘",
        "history": [
            {"role": "user", "content": "안녕하세요"},
            {"role": "assistant", "content": "안녕하세요! 어떤 지역 정보가 궁금하신가요?"}
        ]
    }
    response = client.post("/api/chat", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "reply" in data
    assert "references" in data
    assert "post_references" in data
    assert isinstance(data["references"], list)
    assert isinstance(data["post_references"], list)

def test_chat_validation_error():
    """
    필수 필드 누락 및 길이 제약 위반에 따른 422 에러 테스트
    """
    # 1. message 필드 누락
    response = client.post("/api/chat", json={"history": []})
    assert response.status_code == 422

    # 2. message 길이 초과 (500자 초과)
    long_message = "가" * 501
    response = client.post("/api/chat", json={"message": long_message})
    assert response.status_code == 422

def test_chat_missing_restaurant(mock_openai_chat):
    """
    음식점 추천 문의 시 미보유 답변 제공 여부 테스트
    """
    # mock response 내용을 데이터 미보유 상황에 맞게 세팅
    mock_openai_chat.return_value.choices[0].message.content = (
        "죄송합니다. 현재 음식점 데이터는 제공되지 않습니다. 대신 관광지 정보를 안내해 드릴까요?"
    )
    
    request_data = {
        "message": "강남역 주변 맛집 추천해줘"
    }
    response = client.post("/api/chat", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "음식점" in data["reply"] or "맛집" in data["reply"] or "제공되지 않습니다" in data["reply"]

def test_chat_missing_festival_date(mock_openai_chat):
    """
    축제 일정(날짜) 문의 시 미보유 답변 제공 여부 테스트
    """
    mock_openai_chat.return_value.choices[0].message.content = (
        "죄송합니다. 현재 축제의 시작 및 종료 날짜 정보는 보유하고 있지 않습니다."
    )
    
    request_data = {
        "message": "이번 주 축제 일정 알려줘"
    }
    response = client.post("/api/chat", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "일정" in data["reply"] or "날짜" in data["reply"] or "보유하고 있지 않습니다" in data["reply"]

@patch("openai.resources.chat.completions.AsyncCompletions.create", new_callable=AsyncMock)
def test_chat_upstream_error(mock_create_error):
    """
    OpenAI API 호출 실패 시 502 CHATBOT_UPSTREAM_ERROR 에러 반환 테스트
    """
    # OpenAI API 호출 시 Exception 발생하도록 설정
    mock_create_error.side_effect = Exception("OpenAI API Connection Failed")
    
    request_data = {
        "message": "종로구 관광지 추천해줘"
    }
    response = client.post("/api/chat", json=request_data)
    assert response.status_code == 502
    
    data = response.json()
    assert "detail" in data
    assert data["detail"]["code"] == "CHATBOT_UPSTREAM_ERROR"
    assert "OpenAI" in data["detail"]["message"] or "실패" in data["detail"]["message"]
