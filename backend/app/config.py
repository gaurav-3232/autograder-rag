from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "grader"
    mysql_password: str = "graderpass"
    mysql_database: str = "autograder"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "submissions"
    minio_secure: bool = False
    
    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "reference_docs"
    
    # LLM
    llm_provider: str = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4-turbo-preview"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama2"
    
    # Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
