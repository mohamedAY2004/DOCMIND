"""Health endpoint + harness smoke test."""
from __future__ import annotations


async def test_health_ok(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "uptimeSec" in body
    assert "version" in body


async def test_login_smoke(client, seed):
    """End-to-end smoke: seeded user can log in and call an authed endpoint."""
    await seed.admin(username="smoke_admin", password="secret12")
    resp = await client.post(
        "/api/auth/login", json={"username": "smoke_admin", "password": "secret12"}
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["token"]
    me = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["user"]["username"] == "smoke_admin"
