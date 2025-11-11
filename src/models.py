"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional


class Message(BaseModel):
    """Model for a single message from the API."""
    id: str
    user_id: str
    user_name: str
    timestamp: str
    message: str


class QuestionRequest(BaseModel):
    """Request model for the /ask endpoint."""
    question: str = Field(..., min_length=1, description="The natural language question to answer")


class AnswerResponse(BaseModel):
    """Response model for the /ask endpoint."""
    answer: str = Field(..., description="The answer to the question")
    confidence: Optional[float] = Field(None, description="Confidence score (0-1)")
    source_messages: Optional[list] = Field(None, description="Source messages used to derive the answer")
    metadata: Optional[dict] = Field(None, description="Additional metadata about the answer")


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str
    message_count: int = 0
    metadata: Optional[dict] = None
