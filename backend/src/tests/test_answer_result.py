from models.db_schemes import RetrievedChunk
from services.answer_result import result_from_generation


def chunk(number: int):
    return RetrievedChunk(
        chunk_text=f"Evidence {number}",
        score=0.9,
        chunk_metadata={
            "material_id": f"M-{number}",
            "material_name": f"Lecture {number}.pdf",
            "page": number,
            "section": "Overview",
        },
    )


def test_valid_markers_produce_structured_citations():
    result = result_from_generation("Claim [1] and another [2].", [chunk(1), chunk(2)], source_kind="material")
    assert result.grounding_status == "grounded"
    assert [item["marker"] for item in result.citations] == [1, 2]
    assert result.citations[0]["location"] == {"type": "page", "number": 1}


def test_unknown_markers_are_removed_and_partial_is_reported():
    result = result_from_generation("Supported [1], invented [99].", [chunk(1)], source_kind="material")
    assert "[99]" not in result.text
    assert result.grounding_status == "partially_grounded"
    assert len(result.citations) == 1


def test_no_markers_is_ungrounded_and_no_chunks_is_no_context():
    assert result_from_generation("No citation", [chunk(1)], source_kind="material").grounding_status == "ungrounded"
    assert result_from_generation("No evidence", [], source_kind="material").grounding_status == "no_context"
