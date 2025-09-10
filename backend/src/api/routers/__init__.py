"""
API router configuration and organization
"""
from fastapi import APIRouter
from .health import router as health_router
# from .auth import router as auth_router  # Disabled - using Firebase auth
from .voice_agents import router as voice_agents_router
from .knowledge import router as knowledge_router
from .phone import router as phone_router
from ..websocket_routes import router as websocket_router

# Main API router
api_router = APIRouter(prefix="/api/v1")

# Include sub-routers
api_router.include_router(health_router, tags=["health"])
# api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])  # Disabled - using Firebase auth
# api_router.include_router(tenant_router, prefix="/tenants", tags=["tenants"])  # Disabled - using Firebase auth
api_router.include_router(voice_agents_router, tags=["voice-agents"])
api_router.include_router(knowledge_router, tags=["knowledge"])
api_router.include_router(phone_router, tags=["phone"])
api_router.include_router(websocket_router, tags=["websocket"])