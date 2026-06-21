"""Student "Chat with Tutors" roster ordering: latest semester first.

``GET /api/subjects/student`` returns a student's subjects ordered so the most
recent term surfaces on top and older (archived) terms fall below; subjects with
no semester (always-active) trail last. Within one term the order is alphabetical
by title.
"""
from __future__ import annotations

from datetime import date

from tests.conftest import auth_header


async def test_student_subjects_sorted_latest_semester_first(client, seed):
    student = await seed.student()

    old = await seed.semester(
        id="fall-2023", label="Fall 2023", sort_order=1,
        start_date=date(2023, 9, 1), end_date=date(2023, 12, 31),
    )
    new = await seed.semester(
        id="fall-2025", label="Fall 2025", sort_order=3,
        start_date=date(2025, 9, 1), end_date=date(2025, 12, 31),
    )

    # Two subjects in the newest term (exercises the title tiebreaker) ...
    await seed.subject(id="new-b", title="Beta", semester_id=new.id, students=[student])
    await seed.subject(id="new-a", title="Alpha", semester_id=new.id, students=[student])
    # ... one in the older term ...
    await seed.subject(id="old", title="Gamma", semester_id=old.id, students=[student])
    # ... and one with no semester (always-active; sorts last).
    await seed.subject(id="none", title="Delta", semester_id=None, students=[student])

    resp = await client.get("/api/subjects/student", headers=auth_header(student))
    assert resp.status_code == 200
    ids = [row["id"] for row in resp.json()]

    # Newest term first (Alpha before Beta by title), then older term, then undated.
    assert ids == ["new-a", "new-b", "old", "none"]
