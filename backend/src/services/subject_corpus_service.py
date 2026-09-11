"""Subject material manifest shared by chats and instructor previews."""
from repositories.material_repository import MaterialRepository

async def build_subject_corpus(
    session, subject_id: str
) -> tuple[str, list[tuple[str, str]]]:
    """Return ``(manifest_text, [(material_id, name), ...])`` for a subject.

    The text is injected into the prompts; the ``(id, name)`` list is the
    allowlist the planner's source filter is validated/resolved against.
    ``manifest_text`` is ``""`` when there are no processed materials so the
    template's ``$subject_manifest`` slot collapses cleanly.
    """
    materials = await MaterialRepository(session).processed_materials_for_subject(subject_id)
    if not materials:
        return "", []
    shown = list(materials[: 30])
    lines = ["The following materials are indexed for this subject:"]
    lines.extend(f"  - {name}" for _id, name in shown)
    if len(materials) > len(shown):
        lines.append(f"  - ...and {len(materials) - len(shown)} more.")
    lines.append(
        "Only these materials are available to retrieve from. If a topic is "
        "not covered by them, say so instead of inventing an answer."
    )
    return "\n".join(lines), list(materials)
