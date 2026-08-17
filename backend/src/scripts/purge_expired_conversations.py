"""Nightly retention job. Defaults to report-only; deletion requires --delete."""
from __future__ import annotations

import argparse
import asyncio

from db.models import ConversationKind
from repositories.document_file_repository import DocumentFileRepository
from services.rag_service import collection_for_conversation
from services.retention_service import expired_conversations
from services.storage_service import get_storage


async def run(delete: bool) -> int:
    from main import _shutdown, _startup, app
    await _startup()
    count = 0
    try:
        async with app.state.session_maker() as session:
            rows = await expired_conversations(session)
            for conversation in rows:
                count += 1
                print(f"{conversation.id}\t{conversation.kind.value}\t{conversation.expires_at.isoformat()}")
                if not delete:
                    continue
                if conversation.kind == ConversationKind.DOC:
                    files = await DocumentFileRepository(session).list_for_conversation(conversation.id)
                    for item in files:
                        await get_storage().delete(backend=item.storage_backend, key=item.storage_key, local_path=item.storage_path)
                    collection = collection_for_conversation(conversation.id)
                    if await app.state.vectordb_client.is_collection_exists(collection):
                        await app.state.vectordb_client.delete_collection(collection_name=collection)
                await session.delete(conversation)
            if delete:
                await session.commit()
        return count
    finally:
        await _shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--delete", action="store_true", help="Permanently delete expired rows, objects, and private vectors.")
    args = parser.parse_args()
    total = asyncio.run(run(args.delete))
    print(f"{'deleted' if args.delete else 'would_delete'}={total}")
