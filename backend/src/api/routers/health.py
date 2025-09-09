"""
Health check endpoints for API monitoring
"""
from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    timestamp: datetime
    version: str = "1.0.0"


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    Returns the current health status of the API
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now()
    )