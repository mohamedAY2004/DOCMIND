from tests.conftest import auth_header


async def test_readiness_is_advisory_and_reports_setup_gaps(client, seed):
    instructor = await seed.instructor(username="ready_super")
    await seed.subject(id="ready-sub", instructors=[instructor], super_id=instructor)
    response = await client.get(
        "/api/subjects/ready-sub/readiness", headers=auth_header(instructor)
    )
    assert response.status_code == 200
    assert response.json()["state"] == "needs_setup"
    assert "no_processed_materials" in response.json()["reasons"]


async def test_only_super_instructor_can_create_evaluation_case(client, seed):
    super_instructor = await seed.instructor(username="eval_super")
    viewer = await seed.instructor(username="eval_viewer")
    await seed.subject(
        id="eval-sub",
        instructors=[super_instructor, viewer],
        super_id=super_instructor,
    )
    body = {
        "question": "What is recursion?",
        "referenceAnswer": "A function calling itself with a base case.",
        "expectedMaterialIds": [],
        "tags": ["fundamentals"],
        "active": True,
    }
    denied = await client.post(
        "/api/subjects/eval-sub/evaluation-cases",
        json=body,
        headers=auth_header(viewer),
    )
    assert denied.status_code == 403
    created = await client.post(
        "/api/subjects/eval-sub/evaluation-cases",
        json=body,
        headers=auth_header(super_instructor),
    )
    assert created.status_code == 201
