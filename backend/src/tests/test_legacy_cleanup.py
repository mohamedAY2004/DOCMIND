"""Pure filesystem/retirement regressions; no PostgreSQL fixture required."""
import json
import os
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from services.legacy_cleanup_service import LegacyCleanupService, exclusive_file
from tests.fakes import FakeVectorDB


class Inventory:
    def __init__(self, projects, protected=()):
        self.projects, self.protected = projects, protected
        self.fail_delete = False

    async def inventory(self):
        return self.projects[:]

    async def protected_paths(self):
        return [str(path) for path in self.protected]

    async def remove_project(self, project_id):
        if self.fail_delete:
            raise RuntimeError("Interrupted before deleting database metadata")
        self.projects = [p for p in self.projects if p["id"] != project_id]


def project(root, name, number=1):
    file = root / name / "legacy.pdf"
    file.parent.mkdir(parents=True)
    file.write_text("legacy", encoding="utf8")
    return {"id": number, "project_id": name, "chunk_count": 2, "assets": [
        {"id": number, "asset_type": "file", "asset_name": file.name, "asset_config": {"file_path": str(file)}}]}, file


def service(root, inventory):
    vectors = FakeVectorDB()
    vectors.collections = {"collection_old": {}, "tutor_official": {"chunk": "keep"}, "doc_official": {"chunk": "keep"}}
    cleanup = LegacyCleanupService(AsyncMock(), vectors, root)
    cleanup._repo = inventory
    return cleanup, vectors


def test_path_validation_rejects_escapes_protected_official_and_links(tmp_path):
    root = tmp_path / "uploads"
    row, file = project(root, "old")
    with pytest.raises(ValueError, match="outside"):
        exclusive_file(root / ".." / "outside.pdf", root, set())
    with pytest.raises(ValueError, match="protected"):
        exclusive_file(file, root, {file.resolve()})
    with pytest.raises(ValueError, match="official"):
        exclusive_file(root / "materials" / "official.pdf", root, set())
    linked = root / "hardlink.pdf"
    os.link(file, linked)
    with pytest.raises(ValueError, match="exclusive regular"):
        exclusive_file(file, root, set())


def test_path_validation_rejects_a_linked_parent(tmp_path, monkeypatch):
    root = tmp_path / "uploads"
    _, file = project(root, "old")
    original = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda self: self == file.parent or original(self))
    with pytest.raises(ValueError, match="linked"):
        exclusive_file(file, root, set())


async def test_cleanup_is_dry_by_default_and_preserves_official_and_unlisted_files(tmp_path):
    root = tmp_path / "uploads"
    row, file = project(root, "old")
    unknown = file.parent / "unlisted.pdf"
    unknown.write_text("not in inventory", encoding="utf8")
    official = root / "official.pdf"
    official.write_text("official", encoding="utf8")
    inventory = Inventory([row], [official])
    cleanup, vectors = service(root, inventory)
    manifest = tmp_path / "manifest.json"
    report = await cleanup.run(manifest=manifest)
    assert report["projects"][0]["chunk_count"] == 2
    assert file.exists() and len(inventory.projects) == 1
    assert "collection_old" in vectors.collections
    await cleanup.run(apply=True, manifest=manifest)
    assert not file.exists() and not inventory.projects
    assert official.exists() and unknown.exists()
    assert set(vectors.collections) == {"tutor_official", "doc_official"}
    await cleanup.run(apply=True, manifest=manifest)
    assert json.loads(manifest.read_text())["previous_runs"][-1]["projects"][0]["state"] == "complete"


async def test_cleanup_retains_ambiguous_assets_and_their_database_metadata(tmp_path):
    root = tmp_path / "uploads"
    row, file = project(root, "old")
    inventory = Inventory([row], [file])
    cleanup, vectors = service(root, inventory)
    report = await cleanup.run(apply=True, manifest=tmp_path / "manifest.json")
    assert report["blocked"] and file.exists() and inventory.projects
    assert "collection_old" in vectors.collections


async def test_cleanup_resumes_after_files_deleted_without_losing_inventory(tmp_path):
    root = tmp_path / "uploads"
    row, file = project(root, "old")
    inventory = Inventory([row])
    cleanup, _ = service(root, inventory)
    inventory.fail_delete = True
    manifest = tmp_path / "manifest.json"
    with pytest.raises(RuntimeError, match="Interrupted"):
        await cleanup.run(apply=True, manifest=manifest)
    saved = json.loads(manifest.read_text())
    assert saved["projects"][0]["state"] == "files_deleted"
    assert saved["projects"][0]["assets"] and inventory.projects
    assert not file.exists()
    inventory.fail_delete = False
    await cleanup.run(apply=True, manifest=manifest)
    assert not inventory.projects
    assert not file.parent.exists()


async def test_cleanup_revalidates_original_paths_after_inventory(tmp_path, monkeypatch):
    root = tmp_path / "uploads"
    row, file = project(root, "old")
    cleanup, vectors = service(root, Inventory([row]))
    original = Path.is_symlink
    checkpoint = cleanup._checkpoint
    def swap_after_inventory(path, report):
        checkpoint(path, report)
        monkeypatch.setattr(Path, "is_symlink", lambda self: self == file.parent or original(self))
    monkeypatch.setattr(cleanup, "_checkpoint", swap_after_inventory)
    with pytest.raises(ValueError, match="linked"):
        await cleanup.run(apply=True, manifest=tmp_path / "manifest.json")
    assert file.exists() and "collection_old" in vectors.collections
