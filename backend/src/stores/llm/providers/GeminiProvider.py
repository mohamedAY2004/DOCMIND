from ..LLMInterface import LLMInterface
from google import genai
from google.genai import types
from ..LLMEnums import GeminiEnums
import logging
from typing import List, Union

class GeminiProvider(LLMInterface):
    def __init__(self, api_key: str,
                 default_input_max_characters: int = 1000,
                 default_generation_max_tokens: int = 1000,
                 default_temperature: float = 0.1):

        self.api_key = api_key
        self.default_input_max_characters = default_input_max_characters
        self.default_generation_max_tokens = default_generation_max_tokens
        self.default_temperature = default_temperature

        self.generation_model_id = None
        self.embedding_model_id = None
        self.embedding_size = None
        self.enums = GeminiEnums
        self.client = genai.Client(api_key=self.api_key)

        self.logger = logging.getLogger(__name__)

    def set_generation_model(self, model_id: str):
        self.generation_model_id = model_id

    def set_embedding_model(self, model_id: str, embedding_size: int):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size

    def generate_text(self, prompt: str, chat_history: list = None,
                      generation_max_tokens: int = None,
                      temperature: float = None):
        if not self.client:
            self.logger.error("Gemini client was not set")
            return None
        if not self.generation_model_id:
            self.logger.error("Generation model for Gemini wasn't set")
            return None

        generation_max_tokens = generation_max_tokens or self.default_generation_max_tokens
        temperature = temperature if temperature is not None else self.default_temperature

        if chat_history is None:
            chat_history = []

        chat_history.append(self.construct_prompt(prompt, GeminiEnums.USER.value))

        try:
            response = self.client.models.generate_content(
                model=self.generation_model_id,
                contents=chat_history,
                config=types.GenerateContentConfig( 
                    max_output_tokens=generation_max_tokens,
                    temperature=temperature,
                )
            )
        except Exception as e:
            self.logger.error(f"Error generating text with Gemini: {e}")
            return None

        if not response or not response.text:
            self.logger.error("Error generating text with Gemini")
            return None

        chat_history.append(self.construct_prompt(response.text, GeminiEnums.SYSTEM.value))
        return response.text

    def embed_text(self, text: Union[str, List[str]], document_type: str = None):
        if not self.client:
            self.logger.error("Gemini client was not set")
            return None
        if not self.embedding_model_id:
            self.logger.error("Embedding model for Gemini wasn't set")
            return None
        if isinstance(text, str):
            text = [text]
        try:
            response = self.client.models.embed_content(
                model=self.embedding_model_id,
                contents=[self.process_text(t) for t in text if t is not None],
                config=types.EmbedContentConfig(output_dimensionality=self.embedding_size)
            )
        except Exception as e:
            self.logger.error(f"Error embedding text with Gemini: {e}")
            return None

        if not response or not response.embeddings or len(response.embeddings) == 0:
            self.logger.error("Error embedding text with Gemini")
            return None

        return [e.values for e in response.embeddings]

    def construct_prompt(self, prompt: str, role: str):
        return types.Content(
            role=role,
            parts=[types.Part.from_text(text=self.process_text(prompt))],
        )

    def process_text(self, text: str):
        return text.strip()[:self.default_input_max_characters]