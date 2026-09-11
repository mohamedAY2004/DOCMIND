import pytest
from db.models import Message, MessageRole, User, UserRole, UserStatus
from tests.conftest import auth_header


@pytest.mark.parametrize("kind", ["doc", "tutor"])
async def test_history_over_fifty_defaults_to_ascending_and_supports_recent_pages(client, seed, db, kind):
    student = await seed.student()
    if kind == "tutor":
        await seed.subject(id="history", students=[student])
        conversation = await seed.tutor_conversation(student.id, "history")
    else:
        conversation = await seed.doc_conversation(student.id)
    db.add_all([Message(conversation_id=conversation.id, role=MessageRole.USER, text=str(i)) for i in range(120)])
    await db.commit()
    url = f"/api/chat/{kind}/conversations/{conversation.id}/messages"
    ascending = (await client.get(url, params={"pageSize": 50}, headers=auth_header(student))).json()
    assert [item["text"] for item in ascending["items"]] == [str(i) for i in range(50)]
    recent = (await client.get(url, params={"pageSize": 50, "order": "desc"}, headers=auth_header(student))).json()
    assert [item["text"] for item in recent["items"]] == [str(i) for i in range(119, 69, -1)]
    assert (recent["total"], recent["totalPages"]) == (120, 3)
    oldest = (await client.get(url, params={"pageSize": 50, "page": 3, "order": "desc"}, headers=auth_header(student))).json()
    assert [item["text"] for item in oldest["items"]] == [str(i) for i in range(19, -1, -1)]
    invalid = await client.get(url, params={"order": "invalid"}, headers=auth_header(student))
    assert invalid.status_code == 400
    assert invalid.json()["code"] == "VALIDATION_ERROR"


async def test_admin_users_pagination_and_sorting_exceed_previous_cap(client, seed, db):
    admin = await seed.admin()
    db.add_all([User(username=f"bulk{i:04}", name=f"Bulk {i:04}", email=f"bulk{i}@test.local",
                    role=UserRole.STUDENT, status=UserStatus.ACTIVE, password_hash="unused") for i in range(1001)])
    await db.commit()
    response = await client.get("/api/admin/users", headers=auth_header(admin),
                                params={"search": "bulk", "page": 11, "pageSize": 100, "sort": "username:asc"})
    assert response.status_code == 200
    page = response.json()
    assert page["total"] == 1001 and page["totalPages"] == 11
    assert [item["username"] for item in page["items"]] == ["bulk1000"]
