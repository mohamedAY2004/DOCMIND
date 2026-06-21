"""/api/admin/semesters/* CRUD + /api/semesters listing (Tier 1 admin panel)."""
from __future__ import annotations

from tests.conftest import auth_header


async def test_create_semester_returns_derived_state(client, seed):
    admin = await seed.admin()
    payload = {
        "id": "fall-2025",
        "label": "Fall 2025",
        "sortOrder": 5,
        "startDate": "2025-09-01",
        "endDate": "2025-12-20",
    }
    resp = await client.post(
        "/api/admin/semesters", json=payload, headers=auth_header(admin)
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["id"] == "fall-2025"
    assert body["state"] == "archived"  # ended well before "today"
    assert body["isCurrent"] is False


async def test_create_semester_rejects_inverted_window(client, seed):
    admin = await seed.admin()
    payload = {
        "id": "bad-1",
        "label": "Bad",
        "startDate": "2025-12-01",
        "endDate": "2025-01-01",
    }
    resp = await client.post(
        "/api/admin/semesters", json=payload, headers=auth_header(admin)
    )
    assert resp.status_code == 400, resp.text


async def test_create_semester_duplicate_id_conflicts(client, seed):
    admin = await seed.admin()
    await seed.semester(id="dup", label="Dup")
    resp = await client.post(
        "/api/admin/semesters",
        json={"id": "dup", "label": "Dup again"},
        headers=auth_header(admin),
    )
    assert resp.status_code == 409, resp.text


async def test_update_semester_changes_label_and_dates(client, seed):
    admin = await seed.admin()
    await seed.semester(id="sp-26", label="Spring 26", sort_order=1)
    resp = await client.patch(
        "/api/admin/semesters/sp-26",
        json={"label": "Spring 2026", "startDate": "2026-02-01", "endDate": "2026-06-30"},
        headers=auth_header(admin),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["label"] == "Spring 2026"
    assert body["startDate"] == "2026-02-01"


async def test_delete_semester_unassigns_subjects(client, seed):
    admin = await seed.admin()
    instr = await seed.instructor(username="sem_ins")
    await seed.semester(id="gone", label="Gone")
    await seed.subject(
        id="orphan-sub", semester_id="gone", instructors=[instr], super_id=instr
    )

    resp = await client.delete(
        "/api/admin/semesters/gone", headers=auth_header(admin)
    )
    assert resp.status_code == 204, resp.text

    # Subject survives with its semester cleared (FK SET NULL).
    sub = await client.get("/api/subjects/orphan-sub", headers=auth_header(admin))
    assert sub.status_code == 200, sub.text
    assert sub.json()["semesterId"] is None


async def test_semester_writes_require_admin(client, seed):
    instr = await seed.instructor(username="not_admin")
    resp = await client.post(
        "/api/admin/semesters",
        json={"id": "x-1", "label": "X"},
        headers=auth_header(instr),
    )
    assert resp.status_code == 403, resp.text


async def test_list_semesters_visible_to_any_authenticated_user(client, seed):
    student = await seed.student(username="sem_stud")
    await seed.semester(id="ls-1", label="Listed", start_date=None, end_date=None)
    resp = await client.get("/api/semesters", headers=auth_header(student))
    assert resp.status_code == 200, resp.text
    rows = resp.json()
    listed = next((r for r in rows if r["id"] == "ls-1"), None)
    assert listed is not None
    assert listed["state"] == "active"  # null dates ⇒ fail-open active
