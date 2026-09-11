"""Normalize agent and direct RAG generation to delta/result events."""
from helpers.config import get_settings
from services.answer_result import AnswerResult, result_from_generation


async def generate_answer(rag, agent, *, collection, text, source_kind,
                          history=None, subject_name="", subject_manifest="",
                          material_index=None, streaming=True):
    context = {"subject_name": subject_name, "subject_manifest": subject_manifest}
    if source_kind == "document_file":
        context = {}
    if agent is None:
        if streaming:
            async for event in rag.answer_stream(collection, text, limit=5, threshold=0.3, **context):
                yield event
        else:
            yield "result", await rag.answer(collection, text, limit=5, threshold=0.3, **context)
        return

    settings = get_settings()
    kwargs = dict(collection_name=collection, query=text, rag_service=rag, history=history,
                  limit=settings.AGENT_RETRIEVAL_LIMIT, threshold=settings.AGENT_RETRIEVAL_THRESHOLD,
                  **context)
    if source_kind == "material":
        kwargs.update(material_index=material_index or [],
                      source_filter_enabled=settings.AGENT_SOURCE_FILTER_ENABLED)
    result = None
    if streaming and hasattr(agent, "answer_stream"):
        async for kind, payload in agent.answer_stream(**kwargs):
            if kind == "delta":
                yield kind, payload
            else:
                result = payload
    else:
        result = await agent.answer(**kwargs)
        if result.text:
            yield "delta", result.text
    if result is None:
        raise RuntimeError("Agent completed without a result")
    answer = (result_from_generation(result.text or "", result.retrieved, source_kind=source_kind)
              if result.retrieved else AnswerResult(text=result.text or "",
                  grounding_status="no_context" if result.used_retrieval else "ungrounded"))
    yield "result", answer
