"""/api/auth/* — login, logout, me. Includes H4 (logout expiry) regression."""
from __future__ import annotations

from datetime import datetime, timezone


async def test_login_success(client, seed):
    await seed.student(username="alice", password="hunter22")
    resp = await client.post(
        "/api/auth/login", json={"username": "alice", "password": "hunter22"}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["token"]
    assert body["user"]["username"] == "alice"
    assert body["user"]["role"] == "student"
    assert body["redirect"]


async def test_login_wrong_password(client, seed):
    await seed.student(username="bob", password="correct1")
    resp = await client.post(
        "/api/auth/login", json={"username": "bob", "password": "wrong"}
    )
    assert resp.status_code == 401


async def test_login_unknown_user(client):
    resp = await client.post(
        "/api/auth/login", json={"username": "ghost", "password": "whatever"}
    )
    assert resp.status_code == 401


async def test_login_disabled_user(client, seed):
    from db.models import UserStatus

    await seed.student(username="frozen", password="frozen12", status=UserStatus.DISABLED)
    resp = await client.post(
        "/api/auth/login", json={"username": "frozen", "password": "frozen12"}
    )
    assert resp.status_code == 401


async def test_me_requires_token(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


async def test_me_returns_current_user(client, seed):
    user = await seed.instructor(username="prof_x")
    from tests.conftest import auth_header

    resp = await client.get("/api/auth/me", headers=auth_header(user))
    assert resp.status_code == 200
    assert resp.json()["user"]["username"] == "prof_x"
    assert resp.json()["user"]["role"] == "instructor"


async def test_logout_revokes_token_and_sets_real_expiry(client, seed, db):
    """H4: after logout the token is revoked, and the blocklist row's expiry is
    the token's real ``exp`` (not ``now()``)."""
    from sqlalchemy import select

    from db.models import TokenBlocklist
    from helpers.auth import create_access_token, decode_access_token

    user = await seed.student(username="logmeout", password="byebye12")
    token, jti, _exp = create_access_token(sub=user.id, role=user.role.value)
    headers = {"Authorization": f"Bearer {token}"}

    # token works first
    assert (await client.get("/api/auth/me", headers=headers)).status_code == 200

    logout = await client.post("/api/auth/logout", headers=headers)
    assert logout.status_code == 204

    # token is now revoked
    assert (await client.get("/api/auth/me", headers=headers)).status_code == 401

    # blocklist row carries the token's real exp, not ~now()
    row = (
        await db.execute(select(TokenBlocklist).where(TokenBlocklist.jti == jti))
    ).scalar_one()
    token_exp = datetime.fromtimestamp(
        int(decode_access_token(token)["exp"]), tz=timezone.utc
    )
    stored = row.expires_at
    if stored.tzinfo is None:
        stored = stored.replace(tzinfo=timezone.utc)
    assert abs((stored - token_exp).total_seconds()) < 5
    # ...and that expiry is well in the future (would be ~0 under the old bug)
    assert (stored - datetime.now(timezone.utc)).total_seconds() > 60


async def test_student_access_gate_blocks_login(client, seed, db):
    """Student login is blocked when the global student-access flag is off."""
    from db.models import StudentAccessFlag

    db.add(StudentAccessFlag(id=1, enabled=False, message="Closed for maintenance"))
    await db.commit()

    await seed.student(username="gated", password="gated123")
    resp = await client.post(
        "/api/auth/login", json={"username": "gated", "password": "gated123"}
    )
    assert resp.status_code == 403
    assert resp.json()["code"] == "STUDENT_ACCESS_DISABLED"
