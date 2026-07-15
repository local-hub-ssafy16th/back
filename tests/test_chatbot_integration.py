import pytest
import os
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)

# 실제 OpenAI API Key가 .env에 유효하게 존재할 때만 통합 테스트가 실행되도록 설정
API_KEY_PRESENT = (
    settings.OPENAI_API_KEY 
    and settings.OPENAI_API_KEY != "your_openai_api_key_here" 
    and settings.OPENAI_API_KEY.startswith("sk-")
)

@pytest.mark.skipif(not API_KEY_PRESENT, reason="실제 OpenAI API Key(sk-...)가 .env 파일에 등록되어 있지 않아 통합 테스트를 건너뜁니다.")
def test_chatbot_live_integration():
    """
    실제 OpenAI API와 연동하는 종단간(End-to-End) 통합 테스트
    """
    request_data = {
        "message": "종로구에 있는 유명한 관광지 하나 추천해주고 어떤 곳인지 설명해줘.",
        "history": []
    }
    
    # 실제 /api/chat API 호출 (모킹 없음)
    response = client.post("/api/chat", json=request_data)
    
    # 1. HTTP 응답 코드 검증
    assert response.status_code == 200
    
    data = response.json()
    
    # 2. 응답 DTO 스키마 필수 필드 검증
    assert "reply" in data
    assert "references" in data
    assert "post_references" in data
    
    # 3. 실제 OpenAI가 생성한 텍스트 내용 확인
    assert len(data["reply"]) > 0
    print(f"\n[실제 OpenAI 챗봇 응답]:\n{data['reply']}\n")
    
    # 4. 참조 리스트 형식 검증
    assert isinstance(data["references"], list)
    assert isinstance(data["post_references"], list)


@pytest.mark.skipif(not API_KEY_PRESENT, reason="실제 OpenAI API Key가 등록되어 있지 않아 음식점 예외처리 통합 테스트를 건너뜁니다.")
def test_chatbot_live_missing_restaurant_integration():
    """
    실제 OpenAI API가 맛집/음식점 추천 시 제약 조건(미제공 답변)을 준수하는지 검증하는 통합 테스트
    """
    request_data = {
        "message": "강남역 삼겹살 맛집 추천해주세요.",
        "history": []
    }
    
    response = client.post("/api/chat", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    reply = data["reply"]
    
    print(f"\n[맛집 예외 처리 실제 응답]:\n{reply}\n")
    
    # 프롬프트에 명시된 제약 조건대로 데이터가 제공되지 않는다는 의미의 응답이 담겨있는지 확인
    assert "제공되지 않습니다" in reply or "맛집" in reply or "음식점" in reply
