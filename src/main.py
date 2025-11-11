"""
FastAPI application for the Real-time Question Answering system with LLM.
New Pipeline: Question → Extract Name → Fetch Data → Retrieve → LLM Generate
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Literal
import uvicorn

try:
    from config import settings
    from logger import logger
    from models import QuestionRequest, AnswerResponse, HealthResponse
    from qa_engine import RealtimeQAEngine
except ImportError:
    from src.config import settings
    from src.logger import logger
    from src.models import QuestionRequest, AnswerResponse, HealthResponse
    from src.qa_engine import RealtimeQAEngine


# Global instance
qa_engine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    global qa_engine
    
    # Startup
    logger.info("=== Starting Real-time QA System ===")
    try:
        qa_engine = RealtimeQAEngine()
        stats = qa_engine.get_stats()
        logger.info(f"QA Engine initialized successfully")
        logger.info(f"- Retrieval Method: {settings.retrieval_method}")
        logger.info(f"- LLM Model: {settings.llm_model}")
        logger.info(f"- Cached Messages: {stats['total_messages']}")
        logger.info(f"- Known Users: {stats['total_users']}")
        logger.info(f"- LLM Available: {stats['llm_available']}")
    except Exception as e:
        logger.error(f"Failed to initialize QA engine: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Real-time QA System...")


# Create FastAPI app
app = FastAPI(
    title="Real-time Member QA System with LLM",
    description="Natural language QA system using Llama 3.2 LLM and semantic retrieval",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Real-time Member QA System",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "Real-time person name extraction",
            "Dynamic message fetching from external API",
            "Hybrid retrieval (BM25 + Semantic Search)",
            "LLM answer generation (Llama 3.2)",
            "Natural language responses"
        ],
        "endpoints": {
            "/ask": "POST - Ask a question",
            "/health": "GET - Health check",
            "/stats": "GET - System statistics",
            "/docs": "GET - API documentation"
        }
    }


@app.post("/ask", response_model=AnswerResponse, tags=["QA"])
async def ask_question(
    request: QuestionRequest,
    use_cached_data: bool = Query(True, description="Use cached data (True) or fetch fresh (False)")
):
    """
    Answer a natural language question about members.
    
    Pipeline:
    1. Extract person name from question
    2. Fetch their messages (cached or fresh)
    3. Retrieve relevant messages using hybrid retrieval
    4. Generate answer using Llama 3.2 LLM
    
    Args:
        request: Question request with 'question' field
        use_cached_data: If True, use cached messages; if False, fetch fresh from API
        
    Returns:
        AnswerResponse with generated answer and metadata
    """
    try:
        logger.info(f"Received question: {request.question}")
        
        # Use the new real-time QA engine
        result = qa_engine.answer_question(
            question=request.question,
            use_cached_data=use_cached_data
        )
        
        return AnswerResponse(
            answer=result['answer'],
            confidence=result.get('confidence', 0.0),
            metadata={
                'person_name': result.get('person_name'),
                'messages_found': result.get('messages_found', 0),
                'relevant_messages': result.get('relevant_messages', 0),
                'retrieval_method': result.get('retrieval_method', 'hybrid'),
                'llm_model': result.get('llm_model', 'llama3.2:3b'),
                'used_cached_data': use_cached_data
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing question: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing question: {str(e)}"
        )


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Check API health and system status."""
    try:
        stats = qa_engine.get_stats()
        
        return HealthResponse(
            status="healthy",
            message_count=stats['total_messages'],
            metadata={
                'total_users': stats['total_users'],
                'retrieval_method': stats['retrieval_method'],
                'llm_available': stats['llm_available'],
                'llm_model': 'llama3.2:3b'
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            message_count=0,
            metadata={'error': str(e)}
        )


@app.get("/stats", tags=["Statistics"])
async def get_statistics():
    """Get detailed system statistics."""
    try:
        stats = qa_engine.get_stats()
        return {
            "system": {
                "total_messages": stats['total_messages'],
                "total_users": stats['total_users'],
                "retrieval_method": stats['retrieval_method'],
                "llm_available": stats['llm_available'],
                "llm_model": "llama3.2:3b"
            },
            "known_users": stats['known_users'],
            "user_message_counts": stats['user_message_counts']
        }
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users", tags=["Users"])
async def list_users():
    """List all known users in the system."""
    try:
        stats = qa_engine.get_stats()
        return {
            "total_users": stats['total_users'],
            "users": stats['known_users']
        }
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/refresh-data", tags=["Admin"])
async def refresh_data_from_api(background_tasks: BackgroundTasks):
    """
    Force refresh data from external API (in-memory cache only).
    
    Fetches fresh data from the API and updates the in-memory cache.
    The local messages_checkpoint.ndjson file remains unchanged as the source of truth.
    On next server restart, data will be loaded from the local file again.
    
    This operation runs in the background.
    """
    try:
        def refresh_task():
            logger.info("Starting background data refresh from API...")
            logger.info("Note: Local ndjson file will NOT be modified")
            qa_engine.fetcher.clear_cache()
            messages = qa_engine.fetcher.get_all_messages(force_refresh=True, use_smart_fetch=True)
            logger.info(f"Data refresh complete: {len(messages)} messages fetched and cached in-memory")
        
        background_tasks.add_task(refresh_task)
        
        return {
            "status": "refresh_started",
            "message": "Data refresh from API started in background. In-memory cache will be updated. Local file remains unchanged.",
            "note": "On server restart, data will be reloaded from messages_checkpoint.ndjson"
        }
    except Exception as e:
        logger.error(f"Error starting data refresh: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "main_v2:app",
        host="0.0.0.0",
        port=settings.port,
        reload=False,
        log_level="info"
    )
