"""Application settings.

Every runtime-configurable value lives here. Services read configuration via
`get_settings()` (cached). No module should read environment variables directly.
"""
from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ==================== App ====================
    APP_NAME: str
    APP_VERSION: str
    APP_DESCRIPTION: str
    APP_AUTHOR: str

    # ==================== Files (legacy RAG pipeline) ====================
    FILE_ALLOWED_TYPES: list
    FILE_MAX_SIZE: int
    FILE_DEFAULT_CHUNK_SIZE: int

    # ==================== DocMind upload limits ====================
    # Materials (instructor uploads): PDF / PPTX, up to 50 MiB (spec §7.2).
    UPLOAD_MATERIAL_MAX_MB: int = 50
    # Document chat uploads (student): PDF / PPTX / PNG, up to 25 MiB and max 5 files.
    UPLOAD_DOC_MAX_MB: int = 25
    UPLOAD_DOC_MAX_FILES: int = 5

    # ==================== Database ====================
    DATABASE_URL: str

    # ==================== LLM ====================
    GENERATION_BACKEND: str
    EMBEDDING_BACKEND: str

    GENERATION_MODEL_ID: Optional[str] = None
    EMBEDDING_MODEL_ID: Optional[str] = None
    EMBEDDING_SIZE: Optional[int] = None

    DEFAULT_INPUT_MAX_CHARACTERS: Optional[int] = None
    DEFAULT_GENERATION_MAX_TOKENS: Optional[int] = None
    DEFAULT_GENERATION_TEMPERATURE: Optional[float] = None

    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_URL: Optional[str] = None
    COHERE_API_KEY: Optional[str] = None

    # ==================== VectorDB ====================
    VECTOR_DB_BACKEND: Optional[str] = None
    VECTOR_DB_PATH: Optional[str] = None
    VECTOR_DB_DISTANCE_METHOD: Optional[str] = None

    # ==================== Agent (agentic RAG layer) ====================
    # When AGENT_ENABLED is false, doc-chat and tutor-chat use the classic
    # single-shot RAG path (always retrieve). When true, an agent strategy
    # decides per-turn whether to retrieve and with what query.
    AGENT_ENABLED: bool = False
    # Pluggable strategy name; see stores/agent/AgentEnums.AgentStrategyEnum.
    AGENT_STRATEGY: Optional[str] = "JSON_PLANNER"
    # Low temperature keeps planner decisions stable and JSON-parseable.
    AGENT_PLANNER_TEMPERATURE: float = 0.0
    # Retrieval knobs used by the agent when it decides to call the vector store.
    AGENT_RETRIEVAL_LIMIT: int = 5
    AGENT_RETRIEVAL_THRESHOLD: float = 0.3
    # How many recent conversation messages to feed the planner as context.
    AGENT_HISTORY_TURNS: int = 6

    # ==================== Template ====================
    DEFAULT_LANGUAGE: str = "en"

    # ==================== Auth ====================
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALG: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 720  # 12 hours, per spec §2.1
    BCRYPT_ROUNDS: int = 12

    # ==================== CORS ====================
    # Comma-separated list in the env file, e.g.
    #   CORS_ORIGINS="http://localhost:5173,https://docmind.example.com"
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    # ==================== Misc ====================
    STUDENT_ACCESS_DEFAULT_ENABLED: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance. Cache avoids re-parsing .env per call."""
    return Settings()
