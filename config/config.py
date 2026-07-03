"""
Configuration management for SmartMail AI.

Loads environment variables and provides centralized settings for:
- API credentials (Gmail, Calendar, LLM)
- RAG parameters
- LLM settings
- Logging configuration
- Thresholds and timeouts
"""

from typing import Literal

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ============ API Credentials ============
    gmail_credentials_path: str = Field(
        default="credentials.json",
        description="Path to Gmail OAuth2 credentials file"
    )
    google_calendar_credentials_path: str = Field(
        default="credentials.json",
        description="Path to Google Calendar OAuth2 credentials file"
    )

    # ============ LLM Configuration ============
    llm_provider: Literal["openai", "anthropic", "groq"] = Field(
        default="groq",
        description="LLM provider (openai, anthropic, groq)"
    )
    openai_api_key: str = Field(default="", description="OpenAI API key")
    anthropic_api_key: str = Field(default="", description="Anthropic API key")
    groq_api_key: str = Field(default="", description="Grok API key")
    llm_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="LLM model name"
    )
    llm_temperature: float = Field(default=0.3, description="LLM temperature (0-1)")
    llm_max_tokens: int = Field(default=2000, description="Max tokens per LLM call")
    llm_timeout: int = Field(default=60, description="LLM timeout in seconds")

    # ============ RAG Configuration ============
    vector_db_type: Literal["chroma", "pgvector", "pinecone"] = Field(
        default="chroma",
        description="Vector database type"
    )
    vector_db_path: str = Field(
        default="./data/vector_db",
        description="Path to Chroma vector database"
    )
    openai_api_base_url: str = Field(
        default="",
        description="OpenAI-compatible API base URL for embeddings"
    )
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Embedding model for RAG"
    )
    embedding_batch_size: int = Field(
        default=32,
        description="Batch size for embedding API calls"
    )
    chunk_size: int = Field(default=1000, description="RAG chunk size in tokens")
    chunk_overlap: int = Field(default=100, description="RAG chunk overlap in tokens")
    retrieval_k: int = Field(
        default=5,
        description="Number of documents to retrieve from RAG"
    )
    rerank_enabled: bool = Field(
        default=True,
        description="Enable result re-ranking after retrieval"
    )

    # ============ Processing Thresholds ============
    classification_confidence_threshold: float = Field(
        default=0.8,
        description="Confidence threshold for auto-processing (0-1)"
    )
    reply_confidence_threshold: float = Field(
        default=0.75,
        description="Confidence threshold for auto-sending replies (0-1)"
    )
    calendar_detection_confidence: float = Field(
        default=0.7,
        description="Confidence threshold for calendar event detection (0-1)"
    )

    # ============ API Rate Limiting ============
    gmail_batch_size: int = Field(
        default=10,
        description="Batch size for Gmail API calls"
    )
    gmail_rate_limit_per_minute: int = Field(
        default=60,
        description="Gmail API rate limit per minute"
    )
    calendar_rate_limit_per_minute: int = Field(
        default=60,
        description="Calendar API rate limit per minute"
    )

    # ============ Logging Configuration ============
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )
    log_file: str = Field(
        default="./logs/smartmail.log",
        description="Path to log file"
    )
    log_format: str = Field(
        default="json",
        description="Log format (json or text)"
    )
    max_log_file_size: int = Field(
        default=10485760,
        description="Max log file size in bytes (10MB default)"
    )

    # ============ Database Configuration ============
    sqlite_db_path: str = Field(
        default="./data/smartmail.db",
        description="Path to SQLite database"
    )
    postgres_db_url: str = Field(
        default="postgresql://user:password@localhost/smartmail",
        description="PostgreSQL database URL"
    )

    # ============ Feature Flags ============
    enable_human_review: bool = Field(
        default=True,
        description="Enable human-in-the-loop review"
    )
    enable_auto_calendar_creation: bool = Field(
        default=False,
        description="Enable automatic calendar event creation"
    )
    enable_auto_reply_drafting: bool = Field(
        default=True,
        description="Enable automatic reply drafting"
    )
    dry_run_mode: bool = Field(
        default=False,
        description="Run in dry-run mode (no actual API calls)"
    )

    # ============ LangSmith (Observability) ============
    langsmith_api_key: str = Field(
        default="",
        description="LangSmith API key for observability"
    )
    langsmith_project_name: str = Field(
        default="smartmail-ai",
        description="LangSmith project name"
    )
    enable_langsmith: bool = Field(
        default=False,
        description="Enable LangSmith tracing"
    )

    # ============ Performance Settings ============
    parallel_processing: bool = Field(
        default=True,
        description="Enable parallel processing of emails"
    )
    max_concurrent_tasks: int = Field(
        default=5,
        description="Maximum concurrent tasks"
    )
    cache_enabled: bool = Field(
        default=True,
        description="Enable caching of results"
    )

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
