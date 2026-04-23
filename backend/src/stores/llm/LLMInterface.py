from abc import ABC, abstractmethod
from typing import List, Union
class LLMInterface(ABC):
    
    @abstractmethod
    def set_generation_model(self, model_id: str):
        pass

    @abstractmethod
    def set_embedding_model(self, model_id: str,embedding_size: int):
        pass

    @abstractmethod
    def generate_text(self, prompt: str,chat_history: list=[], generation_max_tokens: int=None, temperature: float=None):
        pass
    
    @abstractmethod
    def embed_text(self, text: Union[str, List[str]], document_type: str = None):
        pass
    
    @abstractmethod
    def construct_prompt(self, prompt: str, role: str):
        pass
   