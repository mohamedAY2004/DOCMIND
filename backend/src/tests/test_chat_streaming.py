from tests.conftest import auth_header


async def test_doc_stream_event_order_and_persistence(client, seed):
    student = await seed.student(username="stream_doc")
    conversation = await seed.doc_conversation(owner_id=student.id)
    response = await client.post(
        f"/api/chat/doc/conversations/{conversation.id}/messages/stream",
        json={"message": "hello"},
        headers=auth_header(student),
    )
    assert response.status_code == 200
    body = response.text
    assert body.index("event: message.created") < body.index("event: answer.delta")
    assert body.index("event: answer.delta") < body.index("event: answer.citations")
    assert body.index("event: answer.citations") < body.index("event: answer.completed")

    messages = await client.get(
        f"/api/chat/doc/conversations/{conversation.id}/messages",
        headers=auth_header(student),
    )
    reply = messages.json()["items"][-1]
    assert reply["generationStatus"] == "complete"
    assert reply["groundingStatus"] == "no_context"


async def test_cancel_generating_reply_is_idempotent(client, seed, db):
    from db.models import GenerationStatus, Message, MessageRole
    student = await seed.student(username="stream_cancel")
    conversation = await seed.doc_conversation(owner_id=student.id)
    reply = Message(
        conversation_id=conversation.id,
        role=MessageRole.DOC,
        text="",
        generation_status=GenerationStatus.GENERATING,
    )
    db.add(reply)
    await db.commit()
    response = await client.post(
        f"/api/chat/messages/{reply.id}/cancel", headers=auth_header(student)
    )
    assert response.status_code == 200
    assert response.json()["generationStatus"] == "cancelled"


async def test_doc_stream_returns_validation_error_before_sse_headers(client, seed):
    from db.models import DocumentFileStatus

    student = await seed.student(username="stream_processing")
    conversation = await seed.doc_conversation(owner_id=student.id)
    await seed.doc_file(conversation.id, status=DocumentFileStatus.PROCESSING)
    response = await client.post(
        f"/api/chat/doc/conversations/{conversation.id}/messages/stream",
        json={"message": "hello"},
        headers=auth_header(student),
    )
    assert response.status_code == 409
    assert response.json()["code"] == "FILES_NOT_READY"
    assert response.headers["content-type"].startswith("application/json")


async def test_doc_stream_uses_agent_when_enabled(client, seed, app):
    from stores.agent.AgentInterface import AgentResult

    class Agent:
        called = False

        async def answer(self, **_kwargs):
            self.called = True
            return AgentResult(text="Agent-selected answer", used_retrieval=False)

    agent = Agent()
    app.state.agent_client = agent
    student = await seed.student(username="stream_agent")
    conversation = await seed.doc_conversation(owner_id=student.id)
    response = await client.post(
        f"/api/chat/doc/conversations/{conversation.id}/messages/stream",
        json={"message": "hello"},
        headers=auth_header(student),
    )
    assert response.status_code == 200
    assert agent.called is True
    assert "Agent-selected answer" in response.text
