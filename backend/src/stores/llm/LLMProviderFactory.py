from helpers.config import Settings
from .LLMEnums import LLMEnums
from .providers import GeminiProvider, OpenAIProvider, CoHereProvider
class LLMProviderFactory:
    def __init__(self,config: Settings):
        self.config = config


    def create(self,provider: str):
        if provider == LLMEnums.GEMINI.value:
            return GeminiProvider(api_key=self.config.GEMINI_API_KEY,
            default_input_max_characters=self.config.DEFAULT_INPUT_MAX_CHARACTERS,
            default_generation_max_tokens=self.config.DEFAULT_GENERATION_MAX_TOKENS,
            default_temperature=self.config.DEFAULT_GENERATION_TEMPERATURE,
            )
        elif provider == LLMEnums.OPENAI.value:
            return OpenAIProvider(api_key=self.config.OPENAI_API_KEY,
            api_url=self.config.OPENAI_API_URL,
            default_input_max_characters=self.config.DEFAULT_INPUT_MAX_CHARACTERS,
            default_generation_max_tokens=self.config.DEFAULT_GENERATION_MAX_TOKENS,
            default_temperature=self.config.DEFAULT_GENERATION_TEMPERATURE,
            )
        elif provider == LLMEnums.COHERE.value:
            return CoHereProvider(api_key=self.config.COHERE_API_KEY,
            default_input_max_characters=self.config.DEFAULT_INPUT_MAX_CHARACTERS,
            default_generation_max_tokens=self.config.DEFAULT_GENERATION_MAX_TOKENS,
            default_temperature=self.config.DEFAULT_GENERATION_TEMPERATURE,
            )