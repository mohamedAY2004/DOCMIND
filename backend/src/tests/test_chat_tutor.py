"""/api/chat/tutor/*. Includes M1 (history ordering) regression."""
from __future__ import annotations

from tests.conftest import auth_header


async def _ready_subject(seed):
    """A subject with a processed material and one enrolled student."""
    instr = await seed.instructor(username="t_ins")
    student = await seed.student(username="t_stud")
    await seed.subject(
        id="tut-sub", instructors=[instr], super_id=instr, students=[student]
    )
    await seed.material("tut-sub")  # PROCESSED → subject is "ready"
    return student


async def test_create_and_send(client, seed):
    student = await _ready_subject(seed)
    create = await client.post(
        "/api/chat/tutor/conversations",
        json={"subjectId": "tut-sub"},
        headers=auth_header(student),
    )
    assert create.status_code == 201, create.text
    conv_id = create.json()["id"]

    send = await client.post(
        f"/api/chat/tutor/conversations/{conv_id}/messages",
        json={"message": "Explain recursion"},
        headers=auth_header(student),
    )
    assert send.status_code == 200, send.text
    body = send.json()
    assert body["userMessage"]["text"] == "Explain recursion"
    assert body["reply"]["role"] == "assistant"
    assert body["reply"]["text"]


async def test_create_requires_enrollment(client, seed):
    await _ready_subject(seed)
    outsider = await seed.student(username="t_outsider")
    resp = await client.post(
        "/api/chat/tutor/conversations",
        json={"subjectId": "tut-sub"},
        headers=auth_header(outsider),
    )
    assert resp.status_code == 403


async def test_create_subject_not_ready(client, seed):
    instr = await seed.instructor(username="nr_ins")
    student = await seed.student(username="nr_stud")
    await seed.subject(id="nr-sub", instructors=[instr], super_id=instr, students=[student])
    # no processed material → not ready
    resp = await client.post(
        "/api/chat/tutor/conversations",
        json={"subjectId": "nr-sub"},
        headers=auth_header(student),
    )
    assert resp.status_code == 409


async def test_list_update_delete(client, seed):
    student = await _ready_subject(seed)
    conv = await seed.tutor_conversation(owner_id=student.id, subject_id="tut-sub")

    lst = await client.get("/api/chat/tutor/conversations", headers=auth_header(student))
    assert lst.status_code == 200
    assert "items" in lst.json()

    patch = await client.patch(
        f"/api/chat/tutor/conversations/{conv.id}",
        json={"title": "My Chat"},
        headers=auth_header(student),
    )
    assert patch.status_code == 200
    assert patch.json()["title"] == "My Chat"

    delete = await client.delete(
        f"/api/chat/tutor/conversations/{conv.id}", headers=auth_header(student)
    )
    assert delete.status_code == 204


async def test_messages_not_owner(client, seed):
    student = await _ready_subject(seed)
    other = await seed.student(username="t_other")
    conv = await seed.tutor_conversation(owner_id=student.id, subject_id="tut-sub")
    resp = await client.get(
        f"/api/chat/tutor/conversations/{conv.id}/messages",
        headers=auth_header(other),
    )
    assert resp.status_code == 403


async def test_instructor_cannot_use_tutor(client, seed):
    instr = await seed.instructor(username="t_blocked_ins")
    resp = await client.post(
        "/api/chat/tutor/conversations",
        json={"subjectId": "tut-sub"},
        headers=auth_header(instr),
    )
    assert resp.status_code == 403


async def test_legacy_tutor_reply(client, seed):
    student = await _ready_subject(seed)
    resp = await client.post(
        "/api/chat/tutor/tut-sub",
        json={"message": "hello tutor"},
        headers=auth_header(student),
    )
    assert resp.status_code == 200, resp.text
    assert isinstance(resp.json()["reply"], str)


async def test_history_returns_most_recent_in_order(seed, db):
    """M1: MessageRepository.history returns the LAST N messages, chronologically."""
    from repositories.message_repository import MessageRepository

    student = await seed.student(username="hist_stud")
    instr = await seed.instructor(username="hist_ins")
    await seed.subject(id="hist-sub", instructors=[instr], super_id=instr, students=[student])
    conv = await seed.tutor_conversation(owner_id=student.id, subject_id="hist-sub")

    for i in range(6):
        await seed.message(conv.id, "user", text_=f"m{i}")

    rows = await MessageRepository(db).history(conv.id, limit=3)
    texts = [m.text for m in rows]
    # last 3 messages, oldest→newest
    assert texts == ["m3", "m4", "m5"]
