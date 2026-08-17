import hashlib
import hmac
import time

from helpers.config import get_settings
from db.models import UserStatus


async def test_cookie_login_me_csrf_and_refresh_rotation(client, seed):
    student = await seed.student(username="cookie_student", password="strong-pass")
    login = await client.post(
        "/api/auth/login", json={"username": student.username, "password": "strong-pass"}
    )
    assert login.status_code == 200
    assert client.cookies.get("docmind_access")
    old_refresh = client.cookies.get("docmind_refresh")
    csrf = client.cookies.get("docmind_csrf")

    me = await client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["user"]["id"] == student.id

    rejected = await client.post("/api/auth/refresh")
    assert rejected.status_code == 403
    refreshed = await client.post("/api/auth/refresh", headers={"X-CSRF-Token": csrf})
    assert refreshed.status_code == 200
    assert client.cookies.get("docmind_refresh") != old_refresh

    current_csrf = client.cookies.get("docmind_csrf")
    client.cookies.delete("docmind_refresh")
    client.cookies.set("docmind_refresh", old_refresh)
    replay = await client.post("/api/auth/refresh", headers={"X-CSRF-Token": current_csrf})
    assert replay.status_code == 401


async def test_sso_code_is_state_bound_and_single_use(client, seed, monkeypatch):
    user = await seed.student(username="portal_student")
    settings = get_settings()
    secret = "portal-test-secret-that-is-at-least-32-bytes"
    monkeypatch.setattr(settings, "PORTAL_SSO", True)
    monkeypatch.setattr(settings, "PORTAL_SSO_SECRET", secret)

    start = await client.post("/api/auth/sso/start")
    assert start.status_code == 200
    state = start.json()["state"]
    issued_at = int(time.time())
    signature = hmac.new(
        secret.encode(), f"{state}.{user.id}.{issued_at}".encode(), hashlib.sha256
    ).hexdigest()
    ticket = await client.post(
        "/api/auth/sso/ticket",
        json={"state": state, "userId": user.id, "issuedAt": issued_at, "signature": signature},
    )
    assert ticket.status_code == 200
    code = ticket.json()["code"]

    exchanged = await client.post("/api/auth/sso/exchange", json={"state": state, "code": code})
    assert exchanged.status_code == 200
    assert exchanged.json()["user"]["id"] == user.id
    replay = await client.post("/api/auth/sso/exchange", json={"state": state, "code": code})
    assert replay.status_code == 401


async def test_sso_rejects_disabled_account(client, seed, monkeypatch):
    user = await seed.student(username="disabled_portal", status=UserStatus.DISABLED)
    settings = get_settings()
    secret = "portal-test-secret-that-is-at-least-32-bytes"
    monkeypatch.setattr(settings, "PORTAL_SSO", True)
    monkeypatch.setattr(settings, "PORTAL_SSO_SECRET", secret)
    state = (await client.post("/api/auth/sso/start")).json()["state"]
    issued_at = int(time.time())
    signature = hmac.new(
        secret.encode(), f"{state}.{user.id}.{issued_at}".encode(), hashlib.sha256
    ).hexdigest()
    ticket = await client.post(
        "/api/auth/sso/ticket",
        json={"state": state, "userId": user.id, "issuedAt": issued_at, "signature": signature},
    )
    assert ticket.status_code == 401
