"""Conservative, resumable deletion of data owned by retired debug projects."""
from pathlib import Path
from datetime import datetime, timezone
import json
import os
from repositories.legacy_cleanup_repository import LegacyCleanupRepository


def exclusive_file(candidate: Path, root: Path, protected: set[Path]) -> Path:
    """Validate lexical and resolved paths before unlinking a single file."""
    root = root.absolute()
    candidate = candidate.absolute()
    resolved_root, resolved = root.resolve(), candidate.resolve()
    if not candidate.is_relative_to(root) or not resolved.is_relative_to(resolved_root):
        raise ValueError("outside upload root")
    if resolved == resolved_root or resolved in protected:
        raise ValueError("shared or protected path")
    if any(resolved.is_relative_to(resolved_root / name) for name in ("materials", "doc_chats")):
        raise ValueError("official upload directory")
    current = candidate
    while current != root.parent:
        if current.exists() or current.is_symlink():
            stat = current.lstat()
            if current.is_symlink() or getattr(stat, "st_file_attributes", 0) & 0x400:
                raise ValueError("linked path")
        if current == root:
            break
        current = current.parent
    if candidate.exists() and (not candidate.is_file() or candidate.stat().st_nlink > 1):
        raise ValueError("not an exclusive regular file")
    return resolved


class LegacyCleanupService:
    def __init__(self, session, vector_store, upload_root):
        self._session, self._vectors = session, vector_store
        self._root = Path(upload_root).absolute()
        self._repo = LegacyCleanupRepository(session)

    async def _protected(self):
        return {Path(p).resolve() for p in await self._repo.protected_paths() if p and not p.startswith("s3:")}

    async def run(self, *, apply=False, manifest=None):
        if apply and (manifest is None or self._vectors is None):
            raise ValueError("Applying cleanup requires a durable manifest and connected vector provider")
        manifest = Path(manifest).absolute() if manifest is not None else None
        if manifest is not None and manifest.resolve().is_relative_to(self._root.resolve()):
            raise ValueError("Keep the cleanup manifest outside the upload directory")
        report = {"version": 1, "apply": apply, "started_at": datetime.now(timezone.utc).isoformat(),
                  "projects": [], "blocked": []}
        # Keep past attempts as audit evidence, never as authority for new deletions.
        if manifest is not None and manifest.exists():
            if manifest.is_symlink():
                raise ValueError("Cleanup manifest cannot be a link")
            previous = json.loads(manifest.read_text(encoding="utf8"))
            report["previous_runs"] = previous.pop("previous_runs", []) + [previous]
        protected = await self._protected()
        for project in await self._repo.inventory():
            files, errors = [], []
            for asset in project["assets"]:
                candidate = self._root / project["project_id"] / asset["asset_name"]
                try:
                    if asset["asset_type"] != "file":
                        raise ValueError("unknown asset type")
                    config = asset["asset_config"] or {}
                    raw = config.get("file_path")
                    if raw and Path(raw).absolute() != candidate.absolute():
                        raise ValueError("configured path disagrees with the legacy upload layout")
                    exclusive_file(candidate, self._root, protected)
                    files.append(str(candidate))
                except (ValueError, OSError, AttributeError) as exc:
                    errors.append({"asset": asset["id"], "path": str(candidate), "reason": str(exc)})
            record = {"project": project["id"], "project_id": project["project_id"],
                      "assets": project["assets"], "chunk_count": project["chunk_count"],
                      "collection": f"collection_{project['project_id']}".strip().lower(),
                      "files": files, "state": "blocked" if errors else "inventoried"}
            report["projects"].append(record)
            if errors:
                report["blocked"].append({"project": project["id"], "files": errors})
                continue
            record["collection_exists"] = await self._vectors.is_collection_exists(record["collection"]) if self._vectors else None
        # Inventory every row/path/collection durably before the first mutation.
        self._checkpoint(manifest, report)
        if not apply:
            return report
        for record in report["projects"]:
            if record["state"] == "blocked":
                continue
            try:
                protected = await self._protected()
                # Revalidate original lexical paths, not their previously resolved targets.
                for path in record["files"]:
                    exclusive_file(Path(path), self._root, protected)
                await self._vectors.delete_collection(record["collection"])
                if await self._vectors.is_collection_exists(record["collection"]):
                    raise RuntimeError("Vector collection deletion did not complete")
                record["state"] = "vectors_deleted"
                self._checkpoint(manifest, report)
                for path in record["files"]:
                    candidate = Path(path)
                    exclusive_file(candidate, self._root, await self._protected())
                    candidate.unlink(missing_ok=True)
                    parent = candidate.parent
                    while parent != self._root and parent.is_relative_to(self._root):
                        try:
                            parent.rmdir()  # only empty directories, never recursive deletion
                        except OSError:
                            break
                        parent = parent.parent
                record["state"] = "files_deleted"
                self._checkpoint(manifest, report)
                await self._repo.remove_project(record["project"])
                await self._session.commit()
                record["state"] = "complete"
                self._checkpoint(manifest, report)
            except BaseException:
                # DB metadata survives any interrupted project so a retry can reconstruct it.
                await self._session.rollback()
                self._checkpoint(manifest, report)
                raise
        return report

    @staticmethod
    def _checkpoint(path, report):
        if path is None:
            return
        temporary = path.with_name(path.name + ".tmp")
        if temporary.is_symlink() or path.is_symlink():
            raise ValueError("Cleanup manifest cannot be a link")
        with temporary.open("w", encoding="utf8") as file:
            json.dump(report, file, indent=2)
            file.flush()
            os.fsync(file.fileno())
        temporary.replace(path)
