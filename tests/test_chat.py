import app.chatbot as chatbot_module


class _FakeMessage:
    def __init__(self, content):
        self.content = content


class _FakeChoice:
    def __init__(self, content):
        self.message = _FakeMessage(content)


class _FakeCompletion:
    def __init__(self, content):
        self.choices = [_FakeChoice(content)]


class _FakeCompletions:
    def __init__(self, content=None, exc=None):
        self._content = content
        self._exc = exc

    def create(self, **kwargs):
        if self._exc is not None:
            raise self._exc
        return _FakeCompletion(self._content)


class _FakeChat:
    def __init__(self, completions):
        self.completions = completions


class FakeOpenAIClient:
    def __init__(self, content=None, exc=None, **kwargs):
        self.chat = _FakeChat(_FakeCompletions(content=content, exc=exc))


def test_chat_success_with_location_reference(client, monkeypatch):
    monkeypatch.setattr(
        chatbot_module,
        "OpenAI",
        lambda **kwargs: FakeOpenAIClient(content="종로구에는 여러 관광지가 있습니다."),
    )

    resp = client.post("/api/chat", json={"message": "종로구 관광지 추천해줘"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["reply"] == "종로구에는 여러 관광지가 있습니다."
    assert isinstance(body["references"], list)
    assert isinstance(body["post_references"], list)
    # 종로구 + 관광지 필터에 매칭된 장소가 근거로 포함되어야 한다
    assert len(body["references"]) > 0
    assert all(ref["content_type_id"] == "12" for ref in body["references"])


def test_chat_includes_post_reference(client, monkeypatch, create_post):
    create_post(category="tour", title="이건 유니크한 게시글 제목입니다")
    monkeypatch.setattr(
        chatbot_module,
        "OpenAI",
        lambda **kwargs: FakeOpenAIClient(content="관련 게시글을 찾았습니다."),
    )

    resp = client.post("/api/chat", json={"message": "유니크한 게시글 찾아줘"})
    assert resp.status_code == 200
    body = resp.json()
    assert any(ref["title"] == "이건 유니크한 게시글 제목입니다" for ref in body["post_references"])


def test_chat_upstream_error_returns_502(client, monkeypatch):
    monkeypatch.setattr(
        chatbot_module,
        "OpenAI",
        lambda **kwargs: FakeOpenAIClient(exc=RuntimeError("upstream timeout")),
    )

    resp = client.post("/api/chat", json={"message": "안녕하세요"})
    assert resp.status_code == 502
    assert resp.json()["detail"]["code"] == "CHATBOT_UPSTREAM_ERROR"


def test_chat_message_length_validation(client):
    resp = client.post("/api/chat", json={"message": ""})
    assert resp.status_code == 422

    resp = client.post("/api/chat", json={"message": "a" * 501})
    assert resp.status_code == 422


def test_chat_history_truncated_to_last_10_turns(client, monkeypatch):
    captured = {}

    def _create(**kwargs):
        captured["messages"] = kwargs["messages"]
        return _FakeCompletion("ok")

    fake_completions = _FakeCompletions()
    fake_completions.create = _create
    monkeypatch.setattr(
        chatbot_module,
        "OpenAI",
        lambda **kwargs: type("C", (), {"chat": _FakeChat(fake_completions)})(),
    )

    history = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"메시지 {i}"}
        for i in range(24)
    ]
    resp = client.post("/api/chat", json={"message": "안녕", "history": history})
    assert resp.status_code == 200

    sent = captured["messages"]
    # system 프롬프트 1개 + history 최근 10턴 + 새 user 메시지 1개
    assert len(sent) == 1 + 10 + 1
    assert sent[1]["content"] == "메시지 14"  # history[-10:]의 첫 항목
    assert sent[-1]["content"] == "안녕"
