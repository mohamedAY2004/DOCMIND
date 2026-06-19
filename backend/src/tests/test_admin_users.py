"""/api/admin/users/* — admin user management."""
from __future__ import annotations

from tests.conftest import auth_header


async def test_create_and_get_user(client, seed):
    admin = await seed.admin()
    payload = {
        "username": "newprof",
        "name": "New Prof",
        "email": "newprof@example.com",
        "role": "instructor",
        "password": "password123",
    }
    create = await client.post("/api/admin/users", json=payload, headers=auth_header(admin))
    assert create.status_code == 201, create.text
    uid = create.json()["id"]
    assert create.json()["role"] == "instructor"

    got = await client.get(f"/api/admin/users/{uid}", headers=auth_header(admin))
    assert got.status_code == 200
    assert got.json()["username"] == "newprof"


async def test_create_duplicate_username_conflict(client, seed):
    admin = await seed.admin()
    payload = {
        "username": "dupe", "name": "A", "email": "a@example.com",
        "role": "student", "password": "password123",
    }
    first = await client.post("/api/admin/users", json=payload, headers=auth_header(admin))
    assert first.status_code == 201
    payload["email"] = "b@example.com"
    second = await client.post("/api/admin/users", json=payload, headers=auth_header(admin))
    assert second.status_code == 409


async def test_create_bad_role_unprocessable(client, seed):
    admin = await seed.admin()
    payload = {
        "username": "weird", "name": "W", "email": "w@example.com",
        "role": "wizard", "password": "password123",
    }
    resp = await client.post("/api/admin/users", json=payload, headers=auth_header(admin))
    # The app maps request-validation errors to 400 with the error envelope.
    assert resp.status_code == 400


async def test_list_users_filter_by_role(client, seed):
    admin = await seed.admin()
    await seed.student(username="s_one")
    await seed.instructor(username="i_one")
    resp = await client.get(
        "/api/admin/users", params={"role": "student"}, headers=auth_header(admin)
    )
    assert resp.status_code == 200
    roles = {u["role"] for u in resp.json()["items"]}
    assert roles <= {"student"}


async def test_update_user(client, seed):
    admin = await seed.admin()
    target = await seed.student(username="to_update")
    resp = await client.patch(
        f"/api/admin/users/{target.id}",
        json={"name": "Updated Name"},
        headers=auth_header(admin),
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Name"


async def test_toggle_status(client, seed):
    admin = await seed.admin()
    target = await seed.student(username="to_disable")
    resp = await client.patch(
        f"/api/admin/users/{target.id}/status",
        json={"status": "disabled"},
        headers=auth_header(admin),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "disabled"


async def test_cannot_disable_self(client, seed):
    admin = await seed.admin()
    resp = await client.patch(
        f"/api/admin/users/{admin.id}/status",
        json={"status": "disabled"},
        headers=auth_header(admin),
    )
    assert resp.status_code == 409


async def test_reset_password(client, seed):
    admin = await seed.admin()
    target = await seed.student(username="to_reset")
    resp = await client.post(
        f"/api/admin/users/{target.id}/reset-password", headers=auth_header(admin)
    )
    assert resp.status_code == 200
    assert len(resp.json()["temporaryPassword"]) >= 8


async def test_delete_user(client, seed):
    admin = await seed.admin()
    target = await seed.student(username="to_delete")
    resp = await client.delete(
        f"/api/admin/users/{target.id}", headers=auth_header(admin)
    )
    assert resp.status_code == 204


async def test_cannot_delete_self(client, seed):
    admin = await seed.admin()
    resp = await client.delete(f"/api/admin/users/{admin.id}", headers=auth_header(admin))
    assert resp.status_code == 409


async def test_enrollment_get_and_set(client, seed):
    admin = await seed.admin()
    student = await seed.student(username="enrollee")
    await seed.subject(id="enr-sub", instructors=[], students=[])

    put = await client.put(
        f"/api/admin/users/{student.id}/subjects",
        json={"subjectIds": ["enr-sub"]},
        headers=auth_header(admin),
    )
    assert put.status_code == 200
    assert any(s["id"] == "enr-sub" for s in put.json())

    got = await client.get(
        f"/api/admin/users/{student.id}/subjects", headers=auth_header(admin)
    )
    assert got.status_code == 200
    assert any(s["id"] == "enr-sub" for s in got.json())


async def test_users_require_admin(client, seed):
    student = await seed.student()
    resp = await client.get("/api/admin/users", headers=auth_header(student))
    assert resp.status_code == 403


async def test_get_unknown_user_404(client, seed):
    admin = await seed.admin()
    resp = await client.get("/api/admin/users/U-NOPE", headers=auth_header(admin))
    assert resp.status_code == 404
