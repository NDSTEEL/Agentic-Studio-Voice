"""
FastAPI application factory and configuration
"""
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
from typing import Callable
import logging

from .routers import api_router


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logging.info("Voice Agent Platform API starting up...")
    yield
    # Shutdown
    logging.info("Voice Agent Platform API shutting down...")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application
    """
    app = FastAPI(
        title="Voice Agent Platform API",
        version="1.0.0",
        description="Backend API for Voice Agent Platform",
        lifespan=lifespan
    )
    
    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:3001"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Add trusted host middleware with testclient support
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["localhost", "127.0.0.1", "*.localhost", "testserver"]
    )
    
    # Include API router
    app.include_router(api_router)
    
    # Add health endpoint at root level
    @app.get("/health")
    async def root_health_check():
        """Root level health check"""
        return {"status": "healthy", "service": "voice-agent-platform"}
    
    # Custom exception handlers
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=404,
            content={"detail": "Not found", "path": str(request.url.path)}
        )
    
    @app.exception_handler(500)
    async def internal_error_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    return app


# Create app instance
app = create_app()