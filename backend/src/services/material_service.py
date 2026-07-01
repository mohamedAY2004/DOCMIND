"""Material upload / list / patch / delete (spec §7)."""
from __future__ import annotations

import asyncio
import logging
import os
import uuid
from pathlib import Path
from typing import List, Literal, Optional

import aiofiles
from fastapi import UploadFile, status
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from db.models import (
    InstructorSubjectRole,
    Material,
    MaterialStatus,
    SemesterState,
    User,
    UserRole,
)
from helpers.config import get_settings
from helpers.errors import APIError, ErrorCode
from repositories.activity_repository import ActivityRepository
from repositories.material_repository import MaterialRepository
from repositories.subject_repository import SubjectRepository
from repositories.user_repository import UserRepository
from schemas.material import MaterialResponse
from services.activity_logger import ActivityLogger
from services.file_service import (
    clean_filename,
    ext_of,
    initials_of,
    materials_dir,
    pretty_date,
    pretty_size,
    random_suffix,
    validate_material_upload,
)
from services.ingestion_service import detect_pdf_encrypted, ingest_file
from services.rag_service import RAGService, collection_for_subject

logger = logging.getLogger("docmind.materials")


def _best_effort_unlink(path) -> None:
    """Remove a file, ignoring the case where it is already gone."""
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass
    except OSError as exc:  # pragma: no cover - best effort
        logger.warning("Failed to remove file %s: %s", path, exc)


class MaterialService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._subjects = SubjectRepository(session)
        self._materials = MaterialRepository(session)
        self._users = UserRepository(session)
        self._activity = ActivityLogger(ActivityRepository(session))

    # ---------- authorization helpers ----------

    async def _ensure_can_read(self, user: User, subject_id: str) -> None:
        if user.role == UserRole.ADMIN:
            if await self._subjects.get(subject_id) is None:
                raise APIError(
                    ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "Subject not found."
                )
            return
        if user.role == UserRole.INSTRUCTOR:
            if await self._subjects.get(subject_id) is None:
                raise APIError(
                    ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "Subject not found."
                )
            if not await self._subjects.is_instructor_of(subject_id, user.id):
                raise APIError(
                    ErrorCode.FORBIDDEN,
                    status.HTTP_403_FORBIDDEN,
                    "You are not assigned to this subject.",
                )
            return
        raise APIError(
            ErrorCode.FORBIDDEN,
            status.HTTP_403_FORBIDDEN,
            "This resource is not available to your role.",
        )

    async def _ensure_on_roster(self, user: User, subject_id: str) -> None:
        if await self._subjects.get(subject_id) is None:
            raise APIError(
                ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "Subject not found."
            )
        if user.role == UserRole.ADMIN:
            return
        if user.role != UserRole.INSTRUCTOR or not await self._subjects.is_instructor_of(
            subject_id, user.id
        ):
            raise APIError(
                ErrorCode.FORBIDDEN,
                status.HTTP_403_FORBIDDEN,
                "You are not assigned to this subject.",
            )

    async def _ensure_can_upload(self, user: User, subject_id: str) -> None:
        """Only the super instructor (or admin) may upload, patch, or delete materials."""
        if await self._subjects.get(subject_id) is None:
            raise APIError(
                ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "Subject not found."
            )
        if user.role == UserRole.ADMIN:
            return
        if user.role != UserRole.INSTRUCTOR:
            raise APIError(
                ErrorCode.FORBIDDEN,
                status.HTTP_403_FORBIDDEN,
                "Only instructors can manage materials.",
            )
        instructor_role = await self._subjects.get_instructor_role(subject_id, user.id)
        if instructor_role is None:
            raise APIError(
                ErrorCode.FORBIDDEN,
                status.HTTP_403_FORBIDDEN,
                "You are not assigned to this subject.",
            )
        if instructor_role != InstructorSubjectRole.SUPER:
            raise APIError(
                ErrorCode.FORBIDDEN,
                status.HTTP_403_FORBIDDEN,
                "Only the super instructor can upload or modify materials.",
            )

    async def _ensure_not_archived(self, subject_id: str) -> None:
        """Reject writes on subjects whose semester has ended (archived).

        Archived terms are read-only for *every* instructor role (super and
        viewer alike): existing materials can still be listed and downloaded,
        but uploads, edits, and deletions are blocked. Mirrors the student
        tutor-chat archive gate in ``TutorChatService``.
        """
        state = await self._subjects.semester_state_for_subject(subject_id)
        if state is SemesterState.ARCHIVED:
            raise APIError(
                ErrorCode.FORBIDDEN,
                status.HTTP_403_FORBIDDEN,
                "This semester is archived; materials are read-only and can "
                "only be downloaded, not changed.",
                details={"semesterState": state.value},
            )

    # ---------- commands ----------

    async def list_for_subject(
        self, caller: User, subject_id: str
    ) -> List[MaterialResponse]:
        await self._ensure_can_read(caller, subject_id)
        rows = await self._materials.list_for_subject(subject_id)
        uploader_ids = {r.uploaded_by_id for r in rows if r.uploaded_by_id}
        users = await self._users.list_by_ids(list(uploader_ids))
        by_id = {u.id: u for u in users}
        return [self._to_response(r, by_id.get(r.uploaded_by_id)) for r in rows]

    async def upload(
        self,
        caller: User,
        subject_id: str,
        upload: UploadFile,
        name_override: Optional[str],
    ) -> tuple[MaterialResponse, dict]:
        """Save the file, insert the DB row, and return ``(response, job)``.

        The ``job`` dict describes the background indexing work the route
        should schedule with ``BackgroundTasks.add_task``.
        """
        await self._ensure_can_upload(caller, subject_id)
        await self._ensure_not_archived(subject_id)
        validate_material_upload(upload)

        display_name = (name_override or upload.filename or "").strip() or "unnamed"
        if await self._materials.name_exists(subject_id, display_name):
            raise APIError(
                ErrorCode.CONFLICT,
                status.HTTP_409_CONFLICT,
                f"A material named '{display_name}' already exists in this subject.",
            )

        directory = materials_dir(subject_id)
        ext = ext_of(upload.filename or "")
        safe = clean_filename(Path(upload.filename or "file").stem) + ext
        storage = directory / f"{random_suffix(16)}_{safe}"

        settings = get_settings()
        max_bytes = settings.UPLOAD_MATERIAL_MAX_MB * 1024 * 1024
        total = 0
        too_large = False
        async with aiofiles.open(storage, "wb") as fh:
            while True:
                data = await upload.read(settings.FILE_DEFAULT_CHUNK_SIZE)
                if not data:
                    break
                total += len(data)
                if total > max_bytes:
                    too_large = True
                    break
                await fh.write(data)
        # Unlink AFTER the handle is closed — Windows refuses to remove a file
        # while it is still open.
        if too_large:
            _best_effort_unlink(storage)
            raise APIError(
                ErrorCode.FILE_TOO_LARGE,
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                "File exceeds the maximum allowed size.",
            )

        if ext == ".pdf" and detect_pdf_encrypted(storage):
            os.unlink(storage)
            raise APIError(
                ErrorCode.FILE_ENCRYPTED,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Encrypted PDFs are not supported.",
            )

        material = Material(
            subject_id=subject_id,
            name=display_name,
            size_bytes=total,
            mime=(upload.content_type or "application/octet-stream").lower(),
            storage_path=str(storage),
            status=MaterialStatus.INDEXING,
            uploaded_by_id=caller.id,
        )
        try:
            await self._materials.add(material)
        except Exception:
            # The file is already on disk but the row failed to persist — don't
            # leave it orphaned. (A commit failure *after* this method returns is
            # a rarer residual; a periodic orphan sweep is the longer-term fix.)
            _best_effort_unlink(storage)
            raise

        await self._activity.record(
            action="Material uploaded",
            actor=caller,
            subject_label=caller.name,
            meta={"subjectId": subject_id, "materialId": material.id},
        )

        job = {
            "material_id": material.id,
            "subject_id": subject_id,
            "path": str(storage),
        }
        return self._to_response(material, caller), job

    async def patch(
        self,
        caller: User,
        subject_id: str,
        material_id: str,
        *,
        name: Optional[str],
        status_value: Optional[Literal["indexing", "processed"]],
    ) -> MaterialResponse:
        await self._ensure_can_upload(caller, subject_id)
        await self._ensure_not_archived(subject_id)
        material = await self._materials.get(material_id)
        if material is None or material.subject_id != subject_id:
            raise APIError(
                ErrorCode.NOT_FOUND,
                status.HTTP_404_NOT_FOUND,
                "Material not found in this subject.",
            )
        if name is not None:
            await self._materials.rename(material_id, name)
            material.name = name
        if status_value is not None:
            await self._materials.set_status(material_id, MaterialStatus(status_value))
            material.status = MaterialStatus(status_value)
        uploader = (
            await self._users.get(material.uploaded_by_id)
            if material.uploaded_by_id
            else None
        )
        return self._to_response(material, uploader)

    async def delete(
        self, caller: User, subject_id: str, material_id: str, rag: RAGService
    ) -> None:
        await self._ensure_can_upload(caller, subject_id)
        await self._ensure_not_archived(subject_id)
        material = await self._materials.get(material_id)
        if material is None or material.subject_id != subject_id:
            raise APIError(
                ErrorCode.NOT_FOUND,
                status.HTTP_404_NOT_FOUND,
                "Material not found in this subject.",
            )
        await self._activity.record(
            action="Material deleted",
            actor=caller,
            subject_label=caller.name,
            meta={"subjectId": subject_id, "materialId": material_id},
        )
        await self._materials.delete(material)
        # Evict the material's chunks from the subject's tutor collection so
        # the tutor stops retrieving deleted content. Runs before the request
        # commits: if it raises, the row delete rolls back and the instructor
        # can retry — never a deleted row with live vectors.
        await rag.delete_material(collection_for_subject(subject_id), material_id)
        try:
            if material.storage_path and os.path.exists(material.storage_path):
                os.unlink(material.storage_path)
        except OSError as exc:
            logger.warning("Failed to remove file %s: %s", material.storage_path, exc)

    async def get_download(
        self, caller: User, subject_id: str, material_id: str
    ) -> tuple[str, str, str]:
        """Resolve a material's on-disk file for download.

        Returns ``(path, download_filename, media_type)``. Any instructor on
        the roster (super *or* viewer) or an admin may download, regardless of
        semester state — retrieving previously uploaded content is the one
        action that stays available on archived terms.
        """
        await self._ensure_can_read(caller, subject_id)
        material = await self._materials.get(material_id)
        if material is None or material.subject_id != subject_id:
            raise APIError(
                ErrorCode.NOT_FOUND,
                status.HTTP_404_NOT_FOUND,
                "Material not found in this subject.",
            )
        if not material.storage_path or not os.path.exists(material.storage_path):
            raise APIError(
                ErrorCode.NOT_FOUND,
                status.HTTP_404_NOT_FOUND,
                "The file for this material is no longer available.",
            )
        ext = ext_of(material.storage_path)
        download_name = material.name
        if ext and not download_name.lower().endswith(ext):
            download_name = f"{download_name}{ext}"
        media_type = material.mime or "application/octet-stream"
        return material.storage_path, download_name, media_type

    # ---------- formatting ----------

    def _to_response(
        self, material: Material, uploader: Optional[User]
    ) -> MaterialResponse:
        uploaded_name = uploader.name if uploader else "Unknown instructor"
        return MaterialResponse(
            id=material.id,
            name=material.name,
            size=pretty_size(material.size_bytes),
            date=pretty_date(material.created_at),
            status=material.status.value,
            uploadedById=material.uploaded_by_id or "",
            uploadedByName=uploaded_name,
            uploadedByInitials=initials_of(uploaded_name),
            sizeBytes=material.size_bytes,
        )


async def index_material_job(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    material_id: str,
    subject_id: str,
    path: str,
    rag_service: RAGService,
) -> None:
    """Background task body. Parses the file and flips status to processed."""
    try:
        chunks = await asyncio.to_thread(ingest_file, Path(path))
        if chunks:
            # Look up the display name so it can be stamped onto every chunk
            # (used for citations and Phase 2 source-scoped retrieval).
            async with session_factory() as session:
                material = await MaterialRepository(session).get(material_id)
                material_name = material.name if material else None
            await rag_service.index_chunks(
                collection_name=collection_for_subject(subject_id),
                chunks=chunks,
                do_reset=False,
                id_prefix=material_id,
                material_name=material_name,
            )
        async with session_factory() as session:
            async with session.begin():
                await MaterialRepository(session).set_status(
                    material_id, MaterialStatus.PROCESSED
                )
    except Exception:  # noqa: BLE001
        logger.exception("Indexing failed for material %s", material_id)
        # Surface the failure on the row so it doesn't stay stuck in INDEXING.
        try:
            async with session_factory() as session:
                async with session.begin():
                    await MaterialRepository(session).set_status(
                        material_id, MaterialStatus.FAILED
                    )
        except Exception:  # noqa: BLE001
            logger.exception(
                "Could not mark material %s as FAILED", material_id
            )
