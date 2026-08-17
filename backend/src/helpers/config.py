"""Application settings.

Every runtime-configurable value lives here. Services read configuration via
`get_settings()` (cached). No module should read environment variables directly.
"""
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/src/.env — resolved absolutely so settings load regardless of the
# current working directory (e.g. when running scripts from seeds/).
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


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
    # Materials (instructor uploads): PDF only, up to 50 MiB (spec §7.2).
    UPLOAD_MATERIAL_MAX_MB: int = 50
    # Document chat uploads (student): PDF only, up to 25 MiB and max 5 files.
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
    # Phase 2: let the planner scope retrieval to specific materials it names.
    # Requires chunks stamped with ``material_id`` (re-index legacy materials
    # first), so it ships OFF — the planner still searches the whole subject.
    AGENT_SOURCE_FILTER_ENABLED: bool = False

    # ==================== Reranking (Phase 3) ====================
    # Cross-encoder reranking of retrieved chunks before synthesis. Over-fetch
    # by recall (vector search), then truncate by precision (reranker) so the
    # small generation model gets fewer, cleaner context chunks. Ships OFF —
    # when disabled the retrieval path is byte-identical to before.
    RERANK_ENABLED: bool = False
    # Pluggable backend; see stores/rerank/RerankEnums.RerankBackendEnum.
    RERANK_BACKEND: Optional[str] = None  # LOCAL_CROSS_ENCODER
    # Cross-encoder model id, e.g. "BAAI/bge-reranker-base".
    RERANK_MODEL_ID: Optional[str] = None
    # Torch device for the local cross-encoder: "cuda" | "cpu" | None (auto).
    RERANK_DEVICE: Optional[str] = None
    # Candidate multiplier: vector search fetches limit * RERANK_OVERFETCH rows,
    # the reranker keeps the best `limit`.
    RERANK_OVERFETCH: int = 3
    # Final cap on reranked chunks; defaults to the caller's `limit` when unset.
    RERANK_TOP_N: Optional[int] = None

    # ==================== MMR diversity (Phase 4) ====================
    # Maximal-Marginal-Relevance prefilter between the vector over-fetch and
    # the cross-encoder: prunes near-duplicate chunks so the reranker (and the
    # generation model) see a diverse pool. Ships OFF — when disabled the
    # retrieval path is byte-identical to before.
    MMR_ENABLED: bool = False
    # Relevance/diversity trade-off: 1.0 = pure relevance, 0.0 = pure diversity.
    # 0.7 keeps ordering relevance-heavy while dropping near-duplicates.
    MMR_LAMBDA: float = 0.7
    # Raw candidate multiplier: vector search fetches keep * MMR_OVERFETCH rows;
    # MMR keeps keep * RERANK_OVERFETCH (or just `keep` when reranking is off).
    MMR_OVERFETCH: int = 5

    # ==================== Template ====================
    DEFAULT_LANGUAGE: str = "en"

    # ==================== Auth ====================
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALG: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 720  # 12 hours, per spec §2.1
    ACCESS_COOKIE_MINUTES: int = 15
    REFRESH_COOKIE_DAYS: int = 7
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"
    LOCAL_AUTH_ENABLED: bool = True
    PORTAL_SSO: bool = False
    PORTAL_SSO_URL: str = "http://localhost:8080/sso"
    PORTAL_SSO_SECRET: str = "change-me-portal-secret"
    REDIS_URL: Optional[str] = None
    ENVIRONMENT: str = "development"
    STRUCTURED_CITATIONS: bool = True
    STREAMING_CHAT: bool = True
    SUBJECT_READINESS: bool = True
    STORAGE_BACKEND: str = "local"
    S3_ENDPOINT_URL: Optional[str] = None
    S3_BUCKET: Optional[str] = None
    S3_REGION: str = "us-east-1"
    S3_ACCESS_KEY_ID: Optional[str] = None
    S3_SECRET_ACCESS_KEY: Optional[str] = None
    RETENTION_DELETE_ENABLED: bool = False
    RETENTION_INTERVAL_SECONDS: int = 86400
    EVALUATION_CASE_RETRIES: int = 3
    EVALUATION_RUN_STALE_MINUTES: int = 15
    AUTH_RATE_LIMIT: int = 10
    AUTH_RATE_WINDOW_SECONDS: int = 60
    CHAT_RATE_LIMIT: int = 60
    CHAT_RATE_WINDOW_SECONDS: int = 60
    UPLOAD_RATE_LIMIT: int = 20
    UPLOAD_RATE_WINDOW_SECONDS: int = 3600
    MAX_CONCURRENT_GENERATIONS: int = 2
    GENERATION_SLOT_TTL_SECONDS: int = 600
    BCRYPT_ROUNDS: int = 12
    # Throttle the per-request ``last_active`` write: only update when the stored
    # timestamp is at least this many seconds stale, to keep read endpoints from
    # issuing a user-row UPDATE on every call.
    LAST_ACTIVE_THROTTLE_SECONDS: int = 300

    # ==================== CORS ====================
    # Comma-separated list in the env file, e.g.
    #   CORS_ORIGINS="http://localhost:5173,https://docmind.example.com"
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        # portal-demo static server (Live Server, python -m http.server, etc.)
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8080",
        "http://localhost:8080",
    ]

    # ==================== Misc ====================
    STUDENT_ACCESS_DEFAULT_ENABLED: bool = True

    # A blank value in the .env (e.g. ``RERANK_TOP_N=``) arrives as an empty
    # string; treat it as "unset" so the field falls back to its default
    # instead of failing int/str parsing.
    @field_validator(
        "RERANK_BACKEND", "RERANK_MODEL_ID", "RERANK_DEVICE", "RERANK_TOP_N",
        mode="before",
    )
    @classmethod
    def _blank_to_none(cls, v):
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

    def validate_production(self) -> None:
        if self.ENVIRONMENT.lower() != "production":
            return
        if self.JWT_SECRET in {
            "change-me-in-production", "CHANGE_ME_32_BYTES_OF_ENTROPY"
        } or len(self.JWT_SECRET) < 32:
            raise RuntimeError("Production JWT_SECRET must be non-default and at least 32 characters.")
        if self.PORTAL_SSO and (
            self.PORTAL_SSO_SECRET == "change-me-portal-secret"
            or len(self.PORTAL_SSO_SECRET) < 32
        ):
            raise RuntimeError("Production PORTAL_SSO_SECRET must be non-default and at least 32 characters.")
        if not self.COOKIE_SECURE:
            raise RuntimeError("COOKIE_SECURE must be true in production.")
        if not self.REDIS_URL:
            raise RuntimeError("REDIS_URL is required in production.")
        if self.STORAGE_BACKEND != "s3":
            raise RuntimeError("STORAGE_BACKEND must be s3 in production.")
        if not self.S3_BUCKET:
            raise RuntimeError("S3_BUCKET is required when STORAGE_BACKEND=s3.")

    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance. Cache avoids re-parsing .env per call."""
    return Settings()
