from types import SimpleNamespace

from stores.agent.strategies.JsonPlannerAgent import JsonPlannerAgent
from stores.llm.LLMEnums import OpenAIEnums


class FakeGeneration:
    enums = OpenAIEnums

    def construct_prompt(self, prompt, role):
        return {"role": role, "content": prompt}

    async def generate_text_async(self, **_kwargs):
        return '{"action":"retrieve","query":"planned query"}'

    async def generate_text_stream_async(self, **_kwargs):
        yield "Grounded "
        yield "answer [1]"


class FakeTemplates:
    def get(self, *, group, key, variables=None):
        if group == "agent" and key == "planner_prompt":
            return "Choose an action"
        if group == "rag" and key == "footer_prompt":
            return "Cite sources"
        return ""


class FakeRag:
    def __init__(self):
        self.query = None
        self.chunk = SimpleNamespace(chunk_text="evidence", chunk_metadata={})

    async def search(self, _collection, query, **_kwargs):
        self.query = query
        return [self.chunk]

    def build_system_prompt(self, _subject, _manifest):
        return "System"

    def build_docs_block(self, _chunks):
        return "[1] evidence"


async def test_json_planner_streams_selected_synthesis_branch():
    rag = FakeRag()
    agent = JsonPlannerAgent(
        generation_client=FakeGeneration(),
        template_parser=FakeTemplates(),
    )
    events = [event async for event in agent.answer_stream(
        collection_name="doc-test",
        query="question",
        rag_service=rag,
    )]
    assert events[0:2] == [("delta", "Grounded "), ("delta", "answer [1]")]
    result = events[-1][1]
    assert rag.query == "planned query"
    assert result.used_retrieval is True
    assert result.text == "Grounded answer [1]"
    assert result.retrieved == [rag.chunk]
