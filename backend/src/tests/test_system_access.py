"""/api/system/student-access (public) + /api/admin/system/student-access (admin)."""
from __future__ import annotations

from tests.conftest import auth_header


async def test_public_get_default_enabled(client):
    resp = await client.get("/api/system/student-access")
    assert resp.status_code == 200
    body = resp.json()
    assert body["enabled"] is True
    assert body["message"] == ""


async def test_admin_can_toggle_and_get_reflects(client, seed):
    admin = await seed.admin()
    patch = await client.patch(
        "/api/admin/system/student-access",
        json={"enabled": False, "message": "Down for now"},
        headers=auth_header(admin),
    )
    assert patch.status_code == 200, patch.text
    assert patch.json()["enabled"] is False
    assert patch.json()["message"] == "Down for now"

    got = await client.get("/api/system/student-access")
    assert got.json()["enabled"] is False
    assert got.json()["message"] == "Down for now"


async def test_non_admin_cannot_toggle(client, seed):
    student = await seed.student()
    resp = await client.patch(
        "/api/admin/system/student-access",
        json={"enabled": False},
        headers=auth_header(student),
    )
    assert resp.status_code == 403


async def test_toggle_requires_auth(client):
    resp = await client.patch(
        "/api/admin/system/student-access", json={"enabled": False}
    )
    assert resp.status_code == 401
