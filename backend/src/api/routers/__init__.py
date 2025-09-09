"""
API router configuration and organization
"""
from fastapi import APIRouter
from .health import router as health_router
from .tenants import router as tenant_router
from .auth import router as auth_router
from .voice_agents import router as voice_agents_router

# Main API router
api_router = APIRouter(prefix="/api/v1")

# Include sub-routers
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(tenant_router, prefix="/tenants", tags=["tenants"])
api_router.include_router(voice_agents_router, prefix="/agents", tags=["voice-agents"])