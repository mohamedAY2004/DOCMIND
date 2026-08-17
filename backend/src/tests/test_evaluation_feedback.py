from tests.conftest import auth_header


async def test_super_instructor_reviews_feedback_and_supplies_reference(client, seed):
    instructor = await seed.instructor(username="feedback_super")
    student = await seed.student(username="feedback_student")
    await seed.subject(
        id="feedback-sub",
        instructors=[instructor],
        super_id=instructor,
        students=[student],
    )
    conversation = await seed.tutor_conversation(
        owner_id=student.id, subject_id="feedback-sub"
    )
    await seed.message(conversation.id, "user", text_="What is a mutex?")
    answer = await seed.message(conversation.id, "assistant", text_="An incorrect answer")
    rated = await client.post(
        f"/api/chat/messages/{answer.id}/feedback",
        json={"feedback": "down", "reason": "incorrect", "comment": "Confuses locks and queues"},
        headers=auth_header(student),
    )
    assert rated.status_code == 200

    review = await client.get(
        "/api/subjects/feedback-sub/feedback?pageSize=50",
        headers=auth_header(instructor),
    )
    assert review.status_code == 200
    row = review.json()["items"][0]
    assert row["question"] == "What is a mutex?"
    assert row["reason"] == "incorrect"

    converted = await client.post(
        f"/api/subjects/feedback-sub/feedback/{row['id']}/evaluation-case",
        json={"referenceAnswer": "A mutex provides mutually exclusive access to a critical section."},
        headers=auth_header(instructor),
    )
    assert converted.status_code == 201
    assert converted.json()["question"] == "What is a mutex?"
    assert converted.json()["referenceAnswer"].startswith("A mutex provides")


async def test_private_document_feedback_is_not_in_subject_review(client, seed):
    instructor = await seed.instructor(username="privacy_super")
    student = await seed.student(username="privacy_student")
    await seed.subject(
        id="privacy-sub",
        instructors=[instructor],
        super_id=instructor,
        students=[student],
    )
    conversation = await seed.doc_conversation(owner_id=student.id)
    answer = await seed.message(conversation.id, "doc", text_="Private document content")
    await client.post(
        f"/api/chat/messages/{answer.id}/feedback",
        json={"feedback": "down", "reason": "unsupported"},
        headers=auth_header(student),
    )

    review = await client.get(
        "/api/subjects/privacy-sub/feedback?pageSize=50",
        headers=auth_header(instructor),
    )
    assert review.status_code == 200
    assert review.json()["items"] == []
