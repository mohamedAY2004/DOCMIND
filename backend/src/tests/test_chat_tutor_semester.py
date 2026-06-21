"""Tier 2A: semester-state gating of tutor chat.

A student may *re-read* conversations in a past-semester subject but may only
start new tutor turns (new conversation / new message / legacy reply) when the
subject's semester is currently active.
"""
from __future__ import annotations

from datetime import date

from tests.conftest import auth_header

_FAR_PAST = (date(2020, 1, 1), date(2020, 5, 1))      # archived
_OPEN = (date(2000, 1, 1), date(2999, 1, 1))          # active regardless of run date
_FAR_FUTURE = (date(2999, 1, 1), date(2999, 5, 1))    # upcoming


async def _enrolled_student(seed, *, sem_id, window, sub_id):
    """A subject in ``window`` with a processed material and one enrolled student.

    The processed material clears ``_ensure_subject_ready`` so the semester gate
    (not the readiness gate) is what the assertions exercise.
    """
    start, end = window
    await seed.semester(id=sem_id, label=sem_id, start_date=start, end_date=end)
    instr = await seed.instructor(username=f"ins_{sub_id}")
    student = await seed.student(username=f"stud_{sub_id}")
    await seed.subject(
        id=sub_id, semester_id=sem_id,
        instructors=[instr], super_id=instr, students=[student],
    )
    await seed.material(sub_id)
    return student


async def test_active_semester_allows_create_and_send(client, seed):
    student = await _enrolled_student(seed, sem_id="act", window=_OPEN, sub_id="act-sub")
    create = await client.post(
        "/api/chat/tutor/conversations",
        json={"subjectId": "act-sub"},
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


async def test_archived_semester_blocks_create(client, seed):
    student = await _enrolled_student(
        seed, sem_id="arch", window=_FAR_PAST, sub_id="arch-sub"
    )
    resp = await client.post(
        "/api/chat/tutor/conversations",
        json={"subjectId": "arch-sub"},
        headers=auth_header(student),
    )
    assert resp.status_code == 403, resp.text
    assert resp.json()["details"]["semesterState"] == "archived"


async def test_archived_semester_blocks_send_but_allows_reread(client, seed):
    student = await _enrolled_student(
        seed, sem_id="arch2", window=_FAR_PAST, sub_id="arch2-sub"
    )
    # History created directly, as if from when the term was live.
    conv = await seed.tutor_conversation(owner_id=student.id, subject_id="arch2-sub")
    await seed.message(conv.id, "user", text_="old question")
    await seed.message(conv.id, "assistant", text_="old answer")

    # Re-reading the past conversation still works.
    read = await client.get(
        f"/api/chat/tutor/conversations/{conv.id}/messages",
        headers=auth_header(student),
    )
    assert read.status_code == 200, read.text
    assert len(read.json()["items"]) == 2

    # A new turn is rejected.
    send = await client.post(
        f"/api/chat/tutor/conversations/{conv.id}/messages",
        json={"message": "a new question"},
        headers=auth_header(student),
    )
    assert send.status_code == 403, send.text


async def test_upcoming_semester_blocks_create(client, seed):
    student = await _enrolled_student(
        seed, sem_id="up", window=_FAR_FUTURE, sub_id="up-sub"
    )
    resp = await client.post(
        "/api/chat/tutor/conversations",
        json={"subjectId": "up-sub"},
        headers=auth_header(student),
    )
    assert resp.status_code == 403, resp.text
    assert resp.json()["details"]["semesterState"] == "upcoming"


async def test_legacy_reply_blocked_on_archived(client, seed):
    student = await _enrolled_student(
        seed, sem_id="arch3", window=_FAR_PAST, sub_id="arch3-sub"
    )
    resp = await client.post(
        "/api/chat/tutor/arch3-sub",
        json={"message": "hello"},
        headers=auth_header(student),
    )
    assert resp.status_code == 403, resp.text


async def test_subject_without_semester_stays_interactive(client, seed):
    """No semester assigned ⇒ fail-open ACTIVE ⇒ new chats allowed (no regression)."""
    instr = await seed.instructor(username="nosem_ins")
    student = await seed.student(username="nosem_stud")
    await seed.subject(
        id="nosem-sub", instructors=[instr], super_id=instr, students=[student]
    )
    await seed.material("nosem-sub")
    resp = await client.post(
        "/api/chat/tutor/conversations",
        json={"subjectId": "nosem-sub"},
        headers=auth_header(student),
    )
    assert resp.status_code == 201, resp.text
