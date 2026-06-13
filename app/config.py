from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    # API Keys
    OPENAI_API_KEY: str = "sk-v1-33ce9310b682303b62de03d7d6a2a884766ca7be5bd4aeaec9eb42a40a922e39"
    OPENAI_BASE_URL: str = "https://api.fastrouter.ai/api/v1"
    JINA_API_KEY: str = "jina_0fd0c481b70e473c8bafa5830ebef694AAxBrIaBqpGDPWQdGiD1ZmcgDXe0"
    CHROMA_API_KEY: str = "ck-AGTYoksPLZ73JXdcnTf2e9M8TWvkntzhDzL8uAER25Gp"
    CHROMA_TENANT: str = "94d52556-8dc0-4627-9fd0-21fc5be2baee"
    CHROMA_DATABASE: str = "rag-system"
    CHROMA_MODE: str = "cloud"  # "local" or "cloud"
    
    # Models
    EMBEDDING_MODEL: str = "jina-embeddings-v5-text-small"
    RERANKER_MODEL: str = "jina-reranker-v2-base-multilingual"
    GENERATION_MODEL: str = "anthropic/claude-opus-4.7"
    
    # Chunking
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    
    # Retrieval
    RETRIEVAL_TOP_K: int = 50
    RERANK_TOP_N: int = 5
    
    # Directories
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    DB_DIR: Path = BASE_DIR / "data" / "db"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.DB_DIR.mkdir(parents=True, exist_ok=True)
