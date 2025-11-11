"""
Configuration management for the QA system.
"""
from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # External API Configuration
    api_base_url: str = "https://november7-730026606190.europe-west1.run.app"
    api_messages_endpoint: str = "/messages/"
    api_timeout: int = 10
    api_max_retries: int = 3
    
    # Server Configuration
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    server_workers: int = 4
    server_reload: bool = False
    
    # Cache Configuration
    cache_dir: str = "./cache"
    cache_ttl: int = 3600  # 1 hour
    
    # Logging Configuration
    log_level: str = "INFO"
    log_dir: str = "./logs"
    log_file: str = "app.log"
    
    # Retrieval Configuration
    retrieval_method: Literal["bm25", "semantic", "hybrid"] = "semantic"
    retrieval_top_k: int = 10
    semantic_model: str = "all-MiniLM-L6-v2"
    semantic_threshold: float = 0.2
    bm25_weight: float = 0.4
    semantic_weight: float = 0.6
    
    # LLM Configuration
    llm_model: str = "llama3.2:3b"
    llm_base_url: str = "http://localhost:11434"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 200
    llm_timeout: int = 30
    
    # Known Users (can be loaded from database in production)
    known_users: list[str] = [
        "Amina Van Den Berg",
        "Armand Dupont",
        "Fatima El-Tahir",
        "Hans Müller",
        "Layla Kawaguchi",
        "Lily O'Sullivan",
        "Lorenzo Cavalli",
        "Sophia Al-Farsi",
        "Thiago Monteiro",
        "Vikram Desai"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
