from tests.conftest import auth_header


async def test_auth_attempt_rate_limit_is_enforced_per_ip(client):
    origin = {"Origin": "http://localhost:5173"}
    for _ in range(10):
        response = await client.post(
            "/api/auth/login",
            json={"username": "missing-user", "password": "wrong-password"},
            headers=origin,
        )
        assert response.status_code == 401
    rejected = await client.post(
        "/api/auth/login",
        json={"username": "missing-user", "password": "wrong-password"},
        headers=origin,
    )
    assert rejected.status_code == 429
    assert rejected.json()["code"] == "RATE_LIMITED"
    assert rejected.headers["Retry-After"] == "60"
    assert rejected.headers["Access-Control-Allow-Origin"] == origin["Origin"]
    assert rejected.headers["X-Request-Id"]


async def test_csrf_rejection_keeps_cors_and_request_id_headers(client):
    client.cookies.set("docmind_access", "present")
    response = await client.post(
        "/api/chat/doc",
        json={"message": "hello"},
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.status_code == 403
    assert response.json()["message"].startswith("CSRF")
    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
    assert response.headers["X-Request-Id"]


async def test_cancel_does_not_consume_chat_turn_budget(client, seed, db, monkeypatch):
    from db.models import GenerationStatus, Message, MessageRole
    from helpers.config import get_settings

    monkeypatch.setattr(get_settings(), "CHAT_RATE_LIMIT", 1)
    student = await seed.student(username="rate_cancel")
    conversation = await seed.doc_conversation(owner_id=student.id)
    reply = Message(
        conversation_id=conversation.id,
        role=MessageRole.DOC,
        text="",
        generation_status=GenerationStatus.GENERATING,
    )
    db.add(reply)
    await db.commit()
    cancelled = await client.post(
        f"/api/chat/messages/{reply.id}/cancel", headers=auth_header(student)
    )
    assert cancelled.status_code == 200

    first_turn = await client.post(
        f"/api/chat/doc/conversations/{conversation.id}/messages",
        json={"message": "first"},
        headers=auth_header(student),
    )
    assert first_turn.status_code == 200
    second_turn = await client.post(
        f"/api/chat/doc/conversations/{conversation.id}/messages",
        json={"message": "second"},
        headers=auth_header(student),
    )
    assert second_turn.status_code == 429
