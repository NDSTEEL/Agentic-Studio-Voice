"""
Database connection utilities for PostgreSQL with async support
"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, text
from typing import AsyncGenerator

# Base for all models
Base = declarative_base()

def get_database_url(async_mode: bool = True) -> str:
    """
    Get database URL from environment variables
    Returns async URL by default for SQLAlchemy 2.0+ support
    """
    # Default development database URL
    default_url = "postgresql://dev_user:dev_password@localhost:5432/voice_agents_dev"
    
    base_url = os.getenv("DATABASE_URL", default_url)
    
    if async_mode and not base_url.startswith("postgresql+asyncpg"):
        # Convert to async URL for asyncpg
        if base_url.startswith("postgresql://"):
            base_url = base_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    return base_url

def create_async_db_engine():
    """Create async database engine"""
    database_url = get_database_url(async_mode=True)
    engine = create_async_engine(
        database_url,
        echo=True if os.getenv("DEBUG") == "true" else False,
        future=True
    )
    return engine

def create_sync_db_engine():
    """Create sync database engine for migrations and testing"""
    database_url = get_database_url(async_mode=False)
    if database_url.startswith("postgresql+asyncpg"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    
    engine = create_engine(
        database_url,
        echo=True if os.getenv("DEBUG") == "true" else False,
        future=True
    )
    return engine

def create_async_session_factory():
    """Create async session factory"""
    engine = create_async_db_engine()
    async_session = async_sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    return async_session

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session"""
    async_session = create_async_session_factory()
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def create_tables():
    """Create all tables using async engine"""
    engine = create_async_db_engine()
    
    # Import all models to ensure they're registered
    from src.models.tenant import Tenant
    from src.models.agent import VoiceAgent  
    from src.models.knowledge import KnowledgeBase
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    await engine.dispose()

def create_tables_sync():
    """Create all tables using sync engine for testing"""
    engine = create_sync_db_engine()
    
    # Import all models to ensure they're registered
    from src.models.tenant import Tenant
    from src.models.agent import VoiceAgent
    from src.models.knowledge import KnowledgeBase
    
    Base.metadata.create_all(engine)
    engine.dispose()

async def test_connection():
    """Test database connection"""
    try:
        engine = create_async_db_engine()
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
    finally:
        await engine.dispose()