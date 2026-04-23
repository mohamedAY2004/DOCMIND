from ..LLMInterface import LLMInterface
from ..LLMEnums import OpenAIEnums
from openai import OpenAI
import logging
from typing import List, Union
class OpenAIProvider(LLMInterface):
    def __init__(self, api_key: str,api_url: str=None,
                        default_input_max_characters: int=1000,
                        default_generation_max_tokens: int=1000,
                        default_temperature: float=0.1):
        self.api_key = api_key
        self.api_url = api_url

        self.default_input_max_characters = default_input_max_characters
        self.default_generation_max_tokens = default_generation_max_tokens
        self.default_temperature = default_temperature

        self.generation_model_id = None

        self.embedding_model_id = None
        self.embedding_size = None
        self.enums = OpenAIEnums
        
        self.client = OpenAI(api_key=self.api_key,
         base_url = self.api_url if self.api_url and len(self.api_url) else None)
        

        self.logger = logging.getLogger(__name__)

    def set_generation_model(self, model_id: str):
        self.generation_model_id = model_id
    
    def set_embedding_model(self, model_id: str,embedding_size: int):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size

    def generate_text(self, prompt: str,chat_history: list=None, generation_max_tokens: int=None, temperature: float=None):
        if not self.client:
            self.logger.error("OpenAI client was not set")
            return None
        if not self.generation_model_id:
            self.logger.error("Generation model for OpenAI wasn't set")
            return None
        generation_max_tokens = generation_max_tokens if generation_max_tokens is not None else self.default_generation_max_tokens
        temperature = temperature if temperature is not None else self.default_temperature
        chat_history = chat_history if chat_history else []
        chat_history.append(self.construct_prompt(prompt, self.enums.USER.value))
        response = self.client.chat.completions.create(
            model=self.generation_model_id,
            messages=chat_history,
            max_tokens=generation_max_tokens,
            temperature=temperature
        )
        content = None
        if not response or not response.choices or len(response.choices) == 0:
            self.logger.error("Error generating text with OpenAI")
            return None
        if not response.choices[0].message.content and not response.choices[0].message.reasoning:
            self.logger.error("Error generating text with OpenAI")
            return None
        else:
            content = response.choices[0].message.content or response.choices[0].message.reasoning
        chat_history.append(self.construct_prompt(content, self.enums.ASSISTANT.value))
        return content

    def process_text(self, text:str):
        return text.strip()[:self.default_input_max_characters]    

    def embed_text(self, text: Union[str, List[str]], document_type: str = None):
        if not self.client:
            self.logger.error("OpenAI client was not set")
            return None
        if not self.embedding_model_id:
            self.logger.error("Embedding model for OpenAI wasn't set")
            return None
        if isinstance(text, str):
            text = [text]
        response=self.client.embeddings.create(
            input=[self.process_text(t) for t in text if t is not None],
            model=self.embedding_model_id,
            dimensions=self.embedding_size
        )

        if not response or not response.data or len(response.data) == 0 or not response.data[0].embedding:
            self.logger.error("Error embedding text with OpenAI")
            return None

        return [d.embedding for d in response.data]
    
    def construct_prompt(self, prompt: str, role: str):
       return{
        "role": role,
        "content": self.process_text(prompt)
       }
    


    