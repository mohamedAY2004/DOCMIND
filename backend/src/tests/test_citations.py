from tests.conftest import auth_header


async def test_document_citation_view_requires_conversation_owner(client, seed, db):
    from db.models import GroundingStatus, Message, MessageRole

    owner = await seed.student(username="cite_owner")
    intruder = await seed.student(username="cite_intruder")
    conversation = await seed.doc_conversation(owner_id=owner.id)
    source = await seed.doc_file(conversation.id, name="notes.pdf")
    message = Message(
        conversation_id=conversation.id,
        role=MessageRole.DOC,
        text="Evidence [1]",
        grounding_status=GroundingStatus.GROUNDED,
        citations=[{
            "id": "cite_test",
            "marker": 1,
            "sourceKind": "document_file",
            "sourceId": source.id,
            "sourceName": source.name,
            "location": {"type": "page", "number": 2},
            "section": "Intro",
            "excerpt": "Evidence",
            "score": 0.9,
        }],
    )
    db.add(message)
    await db.commit()

    allowed = await client.get(
        f"/api/chat/messages/{message.id}/citations/cite_test/view",
        headers=auth_header(owner),
    )
    assert allowed.status_code == 200
    assert allowed.json()["locationNumber"] == 2
    denied = await client.get(
        f"/api/chat/messages/{message.id}/citations/cite_test/view",
        headers=auth_header(intruder),
    )
    assert denied.status_code == 403


async def test_tutor_citation_view_requires_student_conversation_owner(client, seed, db):
    from db.models import GroundingStatus, Message, MessageRole

    owner = await seed.student(username="tutor_cite_owner")
    intruder = await seed.student(username="tutor_cite_intruder")
    subject = await seed.subject(id="sub-citations", students=[owner, intruder])
    material = await seed.material(subject.id)
    conversation = await seed.tutor_conversation(owner.id, subject.id)
    message = Message(
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT,
        text="Evidence [1]",
        grounding_status=GroundingStatus.GROUNDED,
        citations=[{
            "id": "cite_tutor",
            "marker": 1,
            "sourceKind": "material",
            "sourceId": material.id,
            "sourceName": material.name,
            "location": {"type": "page", "number": 1},
            "excerpt": "Evidence",
            "score": 0.9,
        }],
    )
    db.add(message)
    await db.commit()
    allowed = await client.get(
        f"/api/chat/messages/{message.id}/citations/cite_tutor/view",
        headers=auth_header(owner),
    )
    assert allowed.status_code == 200
    denied = await client.get(
        f"/api/chat/messages/{message.id}/citations/cite_tutor/view",
        headers=auth_header(intruder),
    )
    assert denied.status_code == 403
