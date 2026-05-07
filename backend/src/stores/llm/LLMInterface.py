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

    async def generate_text_async(self, prompt: str, chat_history: list = [],
                                  generation_max_tokens: int = None,
                                  temperature: float = None):
        """Async version of generate_text.

        Subclasses that support a native async client should override this.
        The default implementation delegates to the sync version via
        ``asyncio.to_thread`` so the event loop is never blocked.
        """
        import asyncio
        return await asyncio.to_thread(
            self.generate_text, prompt,
            chat_history, generation_max_tokens, temperature,
        )

    async def embed_text_async(self, text: Union[str, List[str]],
                               document_type: str = None):
        """Async version of embed_text.

        Subclasses that support a native async client should override this.
        The default implementation delegates to the sync version via
        ``asyncio.to_thread`` so the event loop is never blocked.
        """
        import asyncio
        return await asyncio.to_thread(self.embed_text, text, document_type)