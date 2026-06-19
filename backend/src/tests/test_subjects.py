"""/api/subjects/*, /api/admin/subjects/*, /api/semesters.

Includes regressions: N2 (one super), N3 (empty roster + super), M4 (wrong-role
id detail), M6 (delete blocked by conversation).
"""
from __future__ import annotations

from tests.conftest import auth_header


async def test_create_subject_assigns_super(client, seed):
    admin = await seed.admin()
    i1 = await seed.instructor(username="ins1")
    i2 = await seed.instructor(username="ins2")
    payload = {
        "id": "cs-101",
        "title": "Intro CS",
        "description": "Fundamentals",
        "courseCode": "CS101",
        "instructorIds": [i1.id, i2.id],
        "superInstructorId": i2.id,
        "studentIds": [],
    }
    resp = await client.post("/api/admin/subjects", json=payload, headers=auth_header(admin))
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert set(body["instructorIds"]) == {i1.id, i2.id}
    # N2: exactly the requested super is assigned
    assert body["superInstructorId"] == i2.id


async def test_create_subject_default_super_is_first(client, seed):
    admin = await seed.admin()
    i1 = await seed.instructor(username="only_ins")
    payload = {
        "id": "cs-102", "title": "T", "description": "D", "courseCode": "C102",
        "instructorIds": [i1.id], "studentIds": [],
    }
    resp = await client.post("/api/admin/subjects", json=payload, headers=auth_header(admin))
    assert resp.status_code == 201, resp.text
    assert resp.json()["superInstructorId"] == i1.id


async def test_create_subject_empty_roster_with_super_rejected(client, seed):
    """N3: superInstructorId supplied with an empty roster → 400."""
    admin = await seed.admin()
    ghost = await seed.instructor(username="ghost_ins")
    payload = {
        "id": "cs-103", "title": "T", "description": "D", "courseCode": "C103",
        "instructorIds": [], "superInstructorId": ghost.id, "studentIds": [],
    }
    resp = await client.post("/api/admin/subjects", json=payload, headers=auth_header(admin))
    assert resp.status_code == 400


async def test_create_subject_wrong_role_id_reported(client, seed):
    """M4: a student id passed as an instructor → 400 with wrong_role_ids detail."""
    admin = await seed.admin()
    stud = await seed.student(username="not_an_ins")
    payload = {
        "id": "cs-104", "title": "T", "description": "D", "courseCode": "C104",
        "instructorIds": [stud.id], "studentIds": [],
    }
    resp = await client.post("/api/admin/subjects", json=payload, headers=auth_header(admin))
    assert resp.status_code == 400
    details = resp.json().get("details") or {}
    assert stud.id in details.get("wrong_role_ids", [])


async def test_create_subject_unknown_id_reported(client, seed):
    admin = await seed.admin()
    payload = {
        "id": "cs-105", "title": "T", "description": "D", "courseCode": "C105",
        "instructorIds": ["U-DOESNOTEXIST"], "studentIds": [],
    }
    resp = await client.post("/api/admin/subjects", json=payload, headers=auth_header(admin))
    assert resp.status_code == 400
    details = resp.json().get("details") or {}
    assert "U-DOESNOTEXIST" in details.get("invalid_instructor_ids", [])


async def test_create_subject_requires_admin(client, seed):
    instructor = await seed.instructor()
    payload = {
        "id": "cs-106", "title": "T", "description": "D", "courseCode": "C106",
        "instructorIds": [], "studentIds": [],
    }
    resp = await client.post(
        "/api/admin/subjects", json=payload, headers=auth_header(instructor)
    )
    assert resp.status_code == 403


async def test_list_admin_subjects(client, seed):
    admin = await seed.admin()
    await seed.subject(id="sub-a", instructors=[], students=[])
    resp = await client.get("/api/admin/subjects", headers=auth_header(admin))
    assert resp.status_code == 200
    assert "items" in resp.json()


async def test_get_subject_access_rules(client, seed):
    admin = await seed.admin()
    instr = await seed.instructor(username="roster_ins")
    enrolled = await seed.student(username="enrolled_s")
    outsider = await seed.student(username="outsider_s")
    await seed.subject(
        id="sub-acc", instructors=[instr], super_id=instr, students=[enrolled]
    )

    assert (await client.get("/api/subjects/sub-acc", headers=auth_header(admin))).status_code == 200
    assert (await client.get("/api/subjects/sub-acc", headers=auth_header(enrolled))).status_code == 200
    assert (await client.get("/api/subjects/sub-acc", headers=auth_header(outsider))).status_code == 403


async def test_list_instructors_shows_roles(client, seed):
    admin = await seed.admin()
    sup = await seed.instructor(username="the_super")
    viewer = await seed.instructor(username="the_viewer")
    await seed.subject(id="sub-roles", instructors=[sup, viewer], super_id=sup, students=[])

    resp = await client.get("/api/subjects/sub-roles/instructors", headers=auth_header(admin))
    assert resp.status_code == 200
    roles = {r["id"]: r["instructorRole"] for r in resp.json()}
    assert roles[sup.id] == "super"
    assert roles[viewer.id] == "viewer"


async def test_list_students_forbidden_for_students(client, seed):
    student = await seed.student()
    await seed.subject(id="sub-stu", instructors=[], students=[student])
    resp = await client.get(
        "/api/subjects/sub-stu/students", headers=auth_header(student)
    )
    assert resp.status_code == 403


async def test_student_route_rejects_instructor(client, seed):
    instructor = await seed.instructor()
    resp = await client.get("/api/subjects/student", headers=auth_header(instructor))
    assert resp.status_code == 403


async def test_update_subject(client, seed):
    admin = await seed.admin()
    await seed.subject(id="sub-upd", instructors=[], students=[])
    resp = await client.patch(
        "/api/admin/subjects/sub-upd",
        json={"title": "Renamed"},
        headers=auth_header(admin),
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Renamed"


async def test_delete_subject(client, seed):
    admin = await seed.admin()
    await seed.subject(id="sub-del", instructors=[], students=[])
    resp = await client.delete("/api/admin/subjects/sub-del", headers=auth_header(admin))
    assert resp.status_code == 204


async def test_delete_subject_blocked_by_conversation(client, seed):
    """M6: a subject with any conversation cannot be deleted (409)."""
    admin = await seed.admin()
    student = await seed.student()
    await seed.subject(id="sub-conv", instructors=[], students=[student])
    await seed.tutor_conversation(owner_id=student.id, subject_id="sub-conv")

    resp = await client.delete("/api/admin/subjects/sub-conv", headers=auth_header(admin))
    assert resp.status_code == 409


async def test_semesters_list_any_authed(client, seed):
    admin = await seed.admin()
    await seed.semester(id="fall-99", label="Fall 99")
    resp = await client.get("/api/semesters", headers=auth_header(admin))
    assert resp.status_code == 200
    assert any(s["id"] == "fall-99" for s in resp.json())
