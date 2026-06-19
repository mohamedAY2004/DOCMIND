"""/api/admin/subjects/stats, /api/admin/feedback, /api/admin/activity,
/api/admin/analytics/daily."""
from __future__ import annotations

from tests.conftest import auth_header


async def test_subject_stats(client, seed):
    admin = await seed.admin()
    await seed.subject(id="stat-sub", instructors=[], students=[])
    await seed.material("stat-sub")
    resp = await client.get("/api/admin/subjects/stats", headers=auth_header(admin))
    assert resp.status_code == 200
    assert "items" in resp.json()
    assert any(s["id"] == "stat-sub" for s in resp.json()["items"])


async def test_feedback_report(client, seed):
    admin = await seed.admin()
    # Build a full feedback row: student → subject → conversation → messages → feedback.
    student = await seed.student(username="fbrep_s")
    instr = await seed.instructor(username="fbrep_i")
    await seed.subject(id="fbrep-sub", instructors=[instr], super_id=instr, students=[student])
    conv = await seed.tutor_conversation(owner_id=student.id, subject_id="fbrep-sub")
    await seed.message(conv.id, "user", text_="q?")
    reply = await seed.message(conv.id, "assistant", text_="a.")
    await seed.feedback(reply.id, student.id, "down")

    resp = await client.get("/api/admin/feedback", headers=auth_header(admin))
    assert resp.status_code == 200
    assert "items" in resp.json()


async def test_feedback_report_filter(client, seed):
    admin = await seed.admin()
    resp = await client.get(
        "/api/admin/feedback", params={"feedback": "down"}, headers=auth_header(admin)
    )
    assert resp.status_code == 200
    assert "items" in resp.json()


async def test_activity_feed(client, seed):
    admin = await seed.admin()
    # generate some activity by creating a subject
    await client.post(
        "/api/admin/subjects",
        json={
            "id": "act-sub", "title": "T", "description": "D", "courseCode": "C",
            "instructorIds": [], "studentIds": [],
        },
        headers=auth_header(admin),
    )
    resp = await client.get("/api/admin/activity", headers=auth_header(admin))
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_activity_limit_bounds(client, seed):
    admin = await seed.admin()
    resp = await client.get(
        "/api/admin/activity", params={"limit": 0}, headers=auth_header(admin)
    )
    assert resp.status_code == 400  # app maps validation errors to 400


async def test_analytics_daily(client, seed):
    admin = await seed.admin()
    resp = await client.get("/api/admin/analytics/daily", headers=auth_header(admin))
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_analytics_days_bounds(client, seed):
    admin = await seed.admin()
    resp = await client.get(
        "/api/admin/analytics/daily", params={"days": 100}, headers=auth_header(admin)
    )
    assert resp.status_code == 400  # app maps validation errors to 400


async def test_admin_endpoints_require_admin(client, seed):
    student = await seed.student()
    for path in (
        "/api/admin/subjects/stats",
        "/api/admin/feedback",
        "/api/admin/activity",
        "/api/admin/analytics/daily",
    ):
        resp = await client.get(path, headers=auth_header(student))
        assert resp.status_code == 403, path
