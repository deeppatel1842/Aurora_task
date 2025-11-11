"""
Application entry point for the Real-time QA System.
Run with: python app.py
"""
import uvicorn
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import settings
from src.logger import logger


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Starting Real-time QA System with LLM")
    logger.info("=" * 60)
    logger.info(f"Server: http://{settings.server_host}:{settings.server_port}")
    logger.info(f"Docs: http://{settings.server_host}:{settings.server_port}/docs")
    logger.info(f"LLM Model: {settings.llm_model}")
    logger.info(f"Retrieval: {settings.retrieval_method}")
    logger.info("=" * 60)
    
    uvicorn.run(
        "src.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.server_reload,
        log_level=settings.log_level.lower()
    )
