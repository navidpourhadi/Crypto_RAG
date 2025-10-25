import os
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env file
ENV = os.getenv("APP_ENV", "development")


class Settings(BaseSettings):
    """
    Configuration settings for the application.
    """

    APP_ENV: str = Field(default=ENV)
    PROJECT_NAME: str = Field(default="Crypto_agent")
    AGENT_NAME: str = Field(default="CryptoAI")
    DEBUG: bool = Field(default=True)

    # API settings
    API_PREFIX: str = Field(default="/api")
    API_VERSION: str = Field(default="v1")

    # CORS settings
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3010", "http://localhost:8010"]
    )

    # MongoDB settings
    MONGO_URI: str = Field(default="mongodb://localhost:27017")
    MONGO_DB_NAME: str = Field(default="Crypto_db")

    # LLM settings
    GOOGLE_API_KEY: str | None = Field(default=None)
    LLM_MODEL: str = Field(default="gemini-2.0-flash")
    LLM_TEMPERATURE: float = Field(default=0.7)

    # Langfuse settings
    LANGFUSE_PUBLIC_KEY: str | None = Field(default=None)
    LANGFUSE_SECRET_KEY: str | None = Field(default=None)
    LANGFUSE_HOST: str = Field(default="https://cloud.langfuse.com")

    # Qdrant Vector Database settings
    QDRANT_URL: str = Field(default="http://localhost:6001")
    QDRANT_API_KEY: str | None = Field(default=None)
    QDRANT_DB_NAME: str = Field(default="Crypto_agent")
    QDRANT_COLLECTION_NAME: str = Field(default="Crypto_news")
    VECTOR_SEARCH_TOP_K: int = Field(default=5)
    VECTOR_SIMILARITY_THRESHOLD: float = Field(default=0.5)

    # Embedding settings
    GEMINI_EMBEDDING_MODEL: str = Field(default="gemini-embedding-001")
    JINA_EMBEDDING_MODEL: str = Field(default="jina-embeddings-v3")
    JINA_API_KEY: str = Field(default="API_KEY")
    JINA_EMBEDDING_URL: str = Field(default="https://api.jina.ai/v1/embeddings")
    EMBEDDING_DIMENSION: int = Field(default=512)

    # Text chunking settings
    LATE_CHUNKING: bool = Field(default=False)
    CHUNK_SIZE: int = Field(default=1000)
    CHUNK_OVERLAP: int = Field(default=100)

    model_config = SettingsConfigDict(
        # Define the configuration for the settings model
        env_file=(".env", ".env.{ENV}"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_ignore_empty=True,
    )


# Create a settings instance
settings = Settings()

if __name__ == "__main__":
    # Print the settings for debugging
    print(settings.model_dump_json(indent=2))
