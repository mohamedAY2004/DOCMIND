"""/api/subjects/{id}/materials + test-bot.

Regressions: H2 (streaming size cap), M5 (indexing failure → FAILED status),
super-only writes (0bf45f5).
"""
from __future__ import annotations

from tests.conftest import auth_header


async def _subject_with_super(seed):
    sup = await seed.instructor(username="super_ins")
    viewer = await seed.instructor(username="viewer_ins")
    await seed.subject(
        id="mat-sub", instructors=[sup, viewer], super_id=sup, students=[]
    )
    return sup, viewer


async def test_list_materials_for_instructor(client, seed):
    sup, _viewer = await _subject_with_super(seed)
    await seed.material("mat-sub", name="Week 1")
    resp = await client.get("/api/subjects/mat-sub/materials", headers=auth_header(sup))
    assert resp.status_code == 200
    assert any(m["name"] == "Week 1" for m in resp.json())


async def test_upload_indexes_and_marks_processed(client, seed, pdf_bytes, monkeypatch):
    sup, _viewer = await _subject_with_super(seed)

    # Deterministic, fast indexing: canned chunks instead of real PDF parsing.
    from services.ingestion_service import IngestedChunk

    monkeypatch.setattr(
        "services.material_service.ingest_file",
        lambda path: [IngestedChunk(text="chunk one", metadata={"page": 1})],
    )

    resp = await client.post(
        "/api/subjects/mat-sub/materials",
        files={"file": ("lecture.pdf", pdf_bytes, "application/pdf")},
        data={"name": "Lecture 1"},
        headers=auth_header(sup),
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] in {"indexing", "processed"}

    # Background indexing job has run (httpx awaits it) → status flips processed.
    listing = await client.get("/api/subjects/mat-sub/materials", headers=auth_header(sup))
    statuses = {m["name"]: m["status"] for m in listing.json()}
    assert statuses["Lecture 1"] == "processed"


async def test_upload_indexing_failure_marks_failed(client, seed, pdf_bytes, monkeypatch):
    """M5: when the indexing job throws, the material ends in FAILED, not stuck."""
    sup, _viewer = await _subject_with_super(seed)

    def boom(path):
        raise RuntimeError("parse exploded")

    monkeypatch.setattr("services.material_service.ingest_file", boom)

    resp = await client.post(
        "/api/subjects/mat-sub/materials",
        files={"file": ("broken.pdf", pdf_bytes, "application/pdf")},
        data={"name": "Broken"},
        headers=auth_header(sup),
    )
    assert resp.status_code == 201, resp.text

    listing = await client.get("/api/subjects/mat-sub/materials", headers=auth_header(sup))
    statuses = {m["name"]: m["status"] for m in listing.json()}
    assert statuses["Broken"] == "failed"


async def test_upload_oversized_rejected(client, seed, pdf_bytes, monkeypatch):
    """H2: the streaming size cap rejects an oversized material with 413.

    We bypass the pre-stream ``file.size`` validation so the streaming loop's
    running-total check (the H2 fix) is what trips.
    """
    sup, _viewer = await _subject_with_super(seed)

    monkeypatch.setattr("services.material_service.validate_material_upload", lambda f: None)
    from helpers.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "UPLOAD_MATERIAL_MAX_MB", 0)  # cap = 0 bytes

    resp = await client.post(
        "/api/subjects/mat-sub/materials",
        files={"file": ("big.pdf", pdf_bytes, "application/pdf")},
        data={"name": "TooBig"},
        headers=auth_header(sup),
    )
    assert resp.status_code == 413


async def test_viewer_instructor_cannot_upload(client, seed, pdf_bytes):
    """Only the super instructor may upload (a viewer → 403)."""
    _sup, viewer = await _subject_with_super(seed)
    resp = await client.post(
        "/api/subjects/mat-sub/materials",
        files={"file": ("x.pdf", pdf_bytes, "application/pdf")},
        data={"name": "Nope"},
        headers=auth_header(viewer),
    )
    assert resp.status_code == 403


async def test_patch_material_status(client, seed):
    sup, _viewer = await _subject_with_super(seed)
    mat = await seed.material("mat-sub", name="Renameable")
    resp = await client.patch(
        f"/api/subjects/mat-sub/materials/{mat.id}",
        json={"name": "Renamed"},
        headers=auth_header(sup),
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed"


async def test_delete_material(client, seed):
    sup, _viewer = await _subject_with_super(seed)
    mat = await seed.material("mat-sub", name="DeleteMe")
    resp = await client.delete(
        f"/api/subjects/mat-sub/materials/{mat.id}", headers=auth_header(sup)
    )
    assert resp.status_code == 204


async def test_delete_material_evicts_chunks(client, seed, app, pdf_bytes, monkeypatch):
    """Deleting a material must also evict its chunks from the subject's tutor
    collection — otherwise the tutor keeps retrieving the deleted content."""
    sup, _viewer = await _subject_with_super(seed)
    from services.ingestion_service import IngestedChunk

    monkeypatch.setattr(
        "services.material_service.ingest_file",
        lambda path: [IngestedChunk(text="stale chunk", metadata={"page": 1})],
    )
    resp = await client.post(
        "/api/subjects/mat-sub/materials",
        files={"file": ("lecture.pdf", pdf_bytes, "application/pdf")},
        data={"name": "ToEvict"},
        headers=auth_header(sup),
    )
    assert resp.status_code == 201, resp.text
    mat_id = resp.json()["id"]

    def chunks_for(material_id):
        store = app.state.vectordb_client.collections.get("tutor_mat-sub", {})
        return [m for _, _, m in store.values() if m.get("material_id") == material_id]

    assert chunks_for(mat_id), "indexing should have stored chunks for the material"

    delete = await client.delete(
        f"/api/subjects/mat-sub/materials/{mat_id}", headers=auth_header(sup)
    )
    assert delete.status_code == 204
    assert not chunks_for(mat_id), "deleted material's chunks must leave the vector store"


async def test_materials_requires_role(client, seed):
    student = await seed.student()
    await seed.subject(id="mat-sub2", instructors=[], students=[student])
    resp = await client.get("/api/subjects/mat-sub2/materials", headers=auth_header(student))
    assert resp.status_code == 403


async def test_test_bot_answers_when_ready(client, seed):
    sup, _viewer = await _subject_with_super(seed)
    await seed.material("mat-sub", name="Indexed", )  # PROCESSED by default
    resp = await client.post(
        "/api/subjects/mat-sub/test-bot",
        json={"message": "What is this about?"},
        headers=auth_header(sup),
    )
    assert resp.status_code == 200, resp.text
    assert isinstance(resp.json()["reply"], str)


async def test_test_bot_not_ready(client, seed):
    sup, _viewer = await _subject_with_super(seed)  # no processed materials
    resp = await client.post(
        "/api/subjects/mat-sub/test-bot",
        json={"message": "hi"},
        headers=auth_header(sup),
    )
    assert resp.status_code == 409
