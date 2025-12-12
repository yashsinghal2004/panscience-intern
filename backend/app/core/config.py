"""Application configuration using Pydantic settings."""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    API_TITLE: str = "RAG Document Q&A API"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Server Configuration
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    
    # Database Configuration
    DATABASE_URL: str = Field(
        default="sqlite:///./data/app.db",
        env="DATABASE_URL"
    )
    
    # File Upload Configuration
    UPLOAD_DIR: str = Field(default="./data/uploads", env="UPLOAD_DIR")
    MAX_FILE_SIZE_MB: int = Field(default=50, env="MAX_FILE_SIZE_MB")
    
    # Embedding Configuration
    EMBEDDING_MODEL: str = Field(
        default="nomic-embed-text-v1",
        env="EMBEDDING_MODEL"
    )
    EMBEDDING_DIMENSION: int = Field(default=768, env="EMBEDDING_DIMENSION")
    NOMIC_API_KEY: Optional[str] = Field(default=None, env="NOMIC_API_KEY")
    
    # Chunking Configuration
    CHUNK_SIZE: int = Field(default=600, env="CHUNK_SIZE")
    CHUNK_OVERLAP: int = Field(default=100, env="CHUNK_OVERLAP")
    CHUNK_TOKENIZER: str = Field(
        default="cl100k_base",
        env="CHUNK_TOKENIZER"
    )
    
    # Retrieval Configuration
    TOP_K_RESULTS: int = Field(default=5, env="TOP_K_RESULTS")
    SIMILARITY_THRESHOLD: float = Field(
        default=0.5,
        env="SIMILARITY_THRESHOLD"
    )
    
    # Vector Store Configuration
    VECTOR_STORE_DIR: str = Field(
        default="./data/vector_store",
        env="VECTOR_STORE_DIR"
    )
    VECTOR_STORE_INDEX_NAME: str = Field(
        default="faiss.index",
        env="VECTOR_STORE_INDEX_NAME"
    )
    
    # LLM Configuration (for synthesis)
    LLM_PROVIDER: str = Field(
        default="openai",
        env="LLM_PROVIDER"
    )  # Options: "openai", "mistral"
    
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(
        default="gpt-3.5-turbo",
        env="OPENAI_MODEL"
    )
    
    MISTRAL_API_KEY: Optional[str] = Field(default=None, env="MISTRAL_API_KEY")
    MISTRAL_MODEL: str = Field(
        default="mistral-medium",
        env="MISTRAL_MODEL"
    )
    
    # CORS Configuration
    CORS_ORIGINS: str = Field(
        default="*",
        env="CORS_ORIGINS"
    )  # Comma-separated list of origins, or "*" for all
    
    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: Optional[str] = Field(default=None, env="LOG_FILE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Create settings instance
settings = Settings()


# Helper function to get CORS origins as list
def get_cors_origins() -> list:
    """Get CORS origins as a list."""
    origins_str = settings.CORS_ORIGINS
    if origins_str == "*":
        return ["*"]
    return [origin.strip() for origin in origins_str.split(",") if origin.strip()]
