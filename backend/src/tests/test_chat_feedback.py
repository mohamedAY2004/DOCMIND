"""/api/chat/messages/{id}/feedback. Includes M2 (delete) regression."""
from __future__ import annotations

from tests.conftest import auth_header


async def _owned_assistant_message(seed, student):
    instr = await seed.instructor(username=f"fb_ins_{student.username}")
    sid = f"fb-{student.username}"
    await seed.subject(id=sid, instructors=[instr], super_id=instr, students=[student])
    conv = await seed.tutor_conversation(owner_id=student.id, subject_id=sid)
    await seed.message(conv.id, "user", text_="q")
    reply = await seed.message(conv.id, "assistant", text_="a")
    return conv, reply


async def test_upsert_feedback_and_hydrate(client, seed):
    student = await seed.student(username="fb1")
    conv, reply = await _owned_assistant_message(seed, student)

    up = await client.post(
        f"/api/chat/messages/{reply.id}/feedback",
        json={"feedback": "up"},
        headers=auth_header(student),
    )
    assert up.status_code == 200, up.text
    assert up.json()["feedback"] == "up"

    msgs = await client.get(
        f"/api/chat/tutor/conversations/{conv.id}/messages",
        headers=auth_header(student),
    )
    fb = {m["id"]: m["feedback"] for m in msgs.json()["items"]}
    assert fb[reply.id] == "up"


async def test_feedback_on_user_message_rejected(client, seed):
    student = await seed.student(username="fb2")
    instr = await seed.instructor(username="fb2_ins")
    await seed.subject(id="fb2-sub", instructors=[instr], super_id=instr, students=[student])
    conv = await seed.tutor_conversation(owner_id=student.id, subject_id="fb2-sub")
    user_msg = await seed.message(conv.id, "user", text_="my question")

    resp = await client.post(
        f"/api/chat/messages/{user_msg.id}/feedback",
        json={"feedback": "down"},
        headers=auth_header(student),
    )
    assert resp.status_code == 400


async def test_delete_feedback_idempotent(client, seed):
    """M2: deleting when no feedback exists is a no-op (204)."""
    student = await seed.student(username="fb3")
    _conv, reply = await _owned_assistant_message(seed, student)
    resp = await client.delete(
        f"/api/chat/messages/{reply.id}/feedback", headers=auth_header(student)
    )
    assert resp.status_code == 204


async def test_delete_feedback_round_trip(client, seed):
    student = await seed.student(username="fb4")
    _conv, reply = await _owned_assistant_message(seed, student)
    await client.post(
        f"/api/chat/messages/{reply.id}/feedback",
        json={"feedback": "down"},
        headers=auth_header(student),
    )
    resp = await client.delete(
        f"/api/chat/messages/{reply.id}/feedback", headers=auth_header(student)
    )
    assert resp.status_code == 204


async def test_delete_others_feedback_forbidden(client, seed):
    """M2: a different user cannot delete someone else's feedback record (403)."""
    owner = await seed.student(username="fb5")
    conv, reply = await _owned_assistant_message(seed, owner)
    await seed.feedback(reply.id, owner.id, "up")

    intruder = await seed.student(username="fb5_intruder")
    resp = await client.delete(
        f"/api/chat/messages/{reply.id}/feedback", headers=auth_header(intruder)
    )
    assert resp.status_code == 403


async def test_feedback_requires_student(client, seed):
    instr = await seed.instructor(username="fb_ins_only")
    resp = await client.post(
        "/api/chat/messages/msg_whatever/feedback",
        json={"feedback": "up"},
        headers=auth_header(instr),
    )
    assert resp.status_code == 403
