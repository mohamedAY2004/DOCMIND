from types import SimpleNamespace

from stores.llm.providers.GeminiProvider import GeminiProvider
from stores.llm.providers.CoHereProvider import CoHereProvider
from stores.llm.providers.OpenAIProvider import OpenAIProvider
from stores.llm.LLMEnums import OpenAIEnums


async def test_gemini_provider_uses_native_streaming_api():
    async def chunks():
        yield SimpleNamespace(text="First ")
        yield SimpleNamespace(text="chunk")

    class Models:
        def __init__(self):
            self.called = False

        async def generate_content_stream(self, **_kwargs):
            self.called = True
            return chunks()

    models = Models()
    provider = object.__new__(GeminiProvider)
    provider.default_input_max_characters = 1000
    provider.default_generation_max_tokens = 1000
    provider.default_temperature = 0.1
    provider.client = SimpleNamespace(aio=SimpleNamespace(models=models))
    provider.set_generation_model("gemini-test")
    output = [part async for part in provider.generate_text_stream_async("hello")]
    assert models.called is True
    assert output == ["First ", "chunk"]


async def test_cohere_provider_uses_native_streaming_api():
    async def chunks():
        yield SimpleNamespace(text="One ")
        yield SimpleNamespace(text="two")

    class Client:
        async def chat_stream(self, **_kwargs):
            async for chunk in chunks():
                yield chunk

    provider = object.__new__(CoHereProvider)
    provider.default_input_max_characters = 1000
    provider.default_generation_max_output_tokens = 1000
    provider.default_generation_temperature = 0.1
    provider.async_client = Client()
    provider.set_generation_model("command-test")
    output = [part async for part in provider.generate_text_stream_async("hello")]
    assert output == ["One ", "two"]


async def test_openai_stream_does_not_expose_reasoning_when_content_arrives():
    async def chunks():
        yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=None, reasoning="private "))])
        yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="public", reasoning=None))])

    class Completions:
        async def create(self, **_kwargs):
            return chunks()

    provider = object.__new__(OpenAIProvider)
    provider.default_input_max_characters = 1000
    provider.default_generation_max_tokens = 1000
    provider.default_temperature = 0.1
    provider.enums = OpenAIEnums
    provider.async_client = SimpleNamespace(
        chat=SimpleNamespace(completions=Completions())
    )
    provider.set_generation_model("openai-test")
    output = [part async for part in provider.generate_text_stream_async("hello")]
    assert output == ["public"]


async def test_openai_stream_uses_reasoning_only_as_whole_response_fallback():
    async def chunks():
        yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=None, reasoning="fallback "))])
        yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=None, reasoning="answer"))])

    class Completions:
        async def create(self, **_kwargs):
            return chunks()

    provider = object.__new__(OpenAIProvider)
    provider.default_input_max_characters = 1000
    provider.default_generation_max_tokens = 1000
    provider.default_temperature = 0.1
    provider.enums = OpenAIEnums
    provider.async_client = SimpleNamespace(
        chat=SimpleNamespace(completions=Completions())
    )
    provider.set_generation_model("openai-test")
    output = [part async for part in provider.generate_text_stream_async("hello")]
    assert output == ["fallback answer"]
