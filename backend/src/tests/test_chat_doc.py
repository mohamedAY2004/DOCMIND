"""/api/chat/doc/* document-chat endpoints."""
from __future__ import annotations

from tests.conftest import auth_header


async def test_create_with_file_indexes_ready(client, seed, pdf_bytes, monkeypatch):
    student = await seed.student(username="doc_stud")
    from services.ingestion_service import IngestedChunk

    monkeypatch.setattr(
        "services.document_chat_service.ingest_file",
        lambda path: [IngestedChunk(text="doc chunk", metadata={})],
    )
    resp = await client.post(
        "/api/chat/doc/conversations",
        files=[("files", ("notes.pdf", pdf_bytes, "application/pdf"))],
        headers=auth_header(student),
    )
    assert resp.status_code == 201, resp.text
    conv_id = resp.json()["conversation"]["id"]
    assert len(resp.json()["files"]) == 1

    files = await client.get(
        f"/api/chat/doc/conversations/{conv_id}/files", headers=auth_header(student)
    )
    assert files.status_code == 200
    assert files.json()[0]["status"] == "ready"


async def test_create_requires_a_file(client, seed):
    student = await seed.student(username="doc_nofile")
    resp = await client.post(
        "/api/chat/doc/conversations",
        files=[("files", ("x.txt", b"hi", "text/plain"))],
        headers=auth_header(student),
    )
    # text/plain is rejected by validate_doc_upload (PDF only)
    assert resp.status_code == 415


async def test_list_messages_and_send(client, seed):
    student = await seed.student(username="doc_send")
    conv = await seed.doc_conversation(owner_id=student.id)

    send = await client.post(
        f"/api/chat/doc/conversations/{conv.id}/messages",
        json={"message": "summarize the doc"},
        headers=auth_header(student),
    )
    assert send.status_code == 200, send.text
    assert send.json()["reply"]["role"] == "doc"

    msgs = await client.get(
        f"/api/chat/doc/conversations/{conv.id}/messages", headers=auth_header(student)
    )
    assert msgs.status_code == 200
    assert msgs.json()["total"] >= 2


async def test_update_conversation(client, seed):
    student = await seed.student(username="doc_upd")
    conv = await seed.doc_conversation(owner_id=student.id)
    resp = await client.patch(
        f"/api/chat/doc/conversations/{conv.id}",
        json={"title": "Renamed Doc"},
        headers=auth_header(student),
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Renamed Doc"


async def test_add_and_delete_file(client, seed, pdf_bytes, monkeypatch):
    student = await seed.student(username="doc_files")
    conv = await seed.doc_conversation(owner_id=student.id)
    await seed.doc_file(conv.id, name="keep.pdf")  # existing first file

    monkeypatch.setattr(
        "services.document_chat_service.ingest_file",
        lambda path: [],
    )
    add = await client.post(
        f"/api/chat/doc/conversations/{conv.id}/files",
        files={"file": ("second.pdf", pdf_bytes, "application/pdf")},
        headers=auth_header(student),
    )
    assert add.status_code == 201, add.text
    new_id = add.json()["id"]

    # now 2 files → can delete one
    delete = await client.delete(
        f"/api/chat/doc/conversations/{conv.id}/files/{new_id}",
        headers=auth_header(student),
    )
    assert delete.status_code == 204


async def test_delete_file_evicts_chunks(client, seed, app, pdf_bytes, monkeypatch):
    """Removing a doc-chat file must also evict its chunks from the
    conversation's collection so chat stops answering from it."""
    student = await seed.student(username="doc_evict")
    conv = await seed.doc_conversation(owner_id=student.id)
    await seed.doc_file(conv.id, name="keep.pdf")  # existing first file

    from services.ingestion_service import IngestedChunk

    monkeypatch.setattr(
        "services.document_chat_service.ingest_file",
        lambda path: [IngestedChunk(text="evict me", metadata={})],
    )
    add = await client.post(
        f"/api/chat/doc/conversations/{conv.id}/files",
        files={"file": ("second.pdf", pdf_bytes, "application/pdf")},
        headers=auth_header(student),
    )
    assert add.status_code == 201, add.text
    file_id = add.json()["id"]

    collection = f"doc_{conv.id}".lower()

    def chunks_for(fid):
        store = app.state.vectordb_client.collections.get(collection, {})
        return [m for _, _, m in store.values() if m.get("material_id") == fid]

    assert chunks_for(file_id), "indexing should have stored chunks for the file"

    delete = await client.delete(
        f"/api/chat/doc/conversations/{conv.id}/files/{file_id}",
        headers=auth_header(student),
    )
    assert delete.status_code == 204
    assert not chunks_for(file_id), "deleted file's chunks must leave the vector store"


async def test_cannot_delete_last_file(client, seed):
    student = await seed.student(username="doc_last")
    conv = await seed.doc_conversation(owner_id=student.id)
    only = await seed.doc_file(conv.id, name="only.pdf")
    resp = await client.delete(
        f"/api/chat/doc/conversations/{conv.id}/files/{only.id}",
        headers=auth_header(student),
    )
    assert resp.status_code == 409


async def test_delete_conversation(client, seed):
    student = await seed.student(username="doc_del")
    conv = await seed.doc_conversation(owner_id=student.id)
    resp = await client.delete(
        f"/api/chat/doc/conversations/{conv.id}", headers=auth_header(student)
    )
    assert resp.status_code == 204


async def test_not_owner_forbidden(client, seed):
    owner = await seed.student(username="doc_owner")
    other = await seed.student(username="doc_intruder")
    conv = await seed.doc_conversation(owner_id=owner.id)
    resp = await client.get(
        f"/api/chat/doc/conversations/{conv.id}/files", headers=auth_header(other)
    )
    assert resp.status_code == 403


async def test_legacy_doc_reply(client, seed):
    student = await seed.student(username="doc_legacy")
    resp = await client.post(
        "/api/chat/doc",
        json={"message": "hello"},
        headers=auth_header(student),
    )
    assert resp.status_code == 200, resp.text
    assert isinstance(resp.json()["reply"], str)
