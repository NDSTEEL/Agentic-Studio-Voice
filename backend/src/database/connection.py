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

async def test_connection_with_timeout(timeout: float = 10.0):
    """Test database connection with timeout"""
    try:
        import asyncio
        engine = create_async_db_engine()
        
        async def _test():
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                return result.scalar() == 1
        
        result = await asyncio.wait_for(_test(), timeout=timeout)
        await engine.dispose()
        return result
    except asyncio.TimeoutError:
        print(f"Database connection timed out after {timeout} seconds")
        return False
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

async def get_postgresql_version():
    """Get PostgreSQL version"""
    try:
        engine = create_async_db_engine()
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            await engine.dispose()
            return version
    except Exception as e:
        print(f"Failed to get PostgreSQL version: {e}")
        return None

def get_pool_config():
    """Get connection pool configuration from environment"""
    import os
    return {
        'min_size': int(os.getenv('DB_POOL_MIN_SIZE', '2')),
        'max_size': int(os.getenv('DB_POOL_MAX_SIZE', '10')),
        'max_queries': int(os.getenv('DB_POOL_MAX_QUERIES', '50000')),
        'max_inactive_connection_lifetime': int(os.getenv('DB_POOL_MAX_INACTIVE_TIME', '300'))
    }

# Connection Pool Implementation
import asyncpg
from typing import Optional

class DatabasePool:
    """Database connection pool wrapper"""
    
    def __init__(self, min_size: int, max_size: int, max_queries: int = 50000, max_inactive_connection_lifetime: int = 300):
        self.min_size = min_size
        self.max_size = max_size
        self.max_queries = max_queries
        self.max_inactive_connection_lifetime = max_inactive_connection_lifetime
        self._pool: Optional[asyncpg.Pool] = None
    
    async def _create_pool(self):
        """Create the actual asyncpg pool"""
        if self._pool is None:
            database_url = get_database_url(async_mode=False)  # asyncpg doesn't need +asyncpg prefix
            if database_url.startswith("postgresql+asyncpg://"):
                database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
            
            self._pool = await asyncpg.create_pool(
                database_url,
                min_size=self.min_size,
                max_size=self.max_size,
                max_queries=self.max_queries,
                max_inactive_connection_lifetime=self.max_inactive_connection_lifetime
            )
    
    async def acquire(self):
        """Acquire connection from pool"""
        if self._pool is None:
            await self._create_pool()
        return await self._pool.acquire()
    
    async def release(self, connection):
        """Release connection back to pool"""
        if self._pool:
            await self._pool.release(connection)
    
    def get_stats(self):
        """Get pool statistics"""
        if self._pool:
            return {
                'size': self._pool.get_size(),
                'idle': self._pool.get_idle_size(),
                'active': self._pool.get_size() - self._pool.get_idle_size()
            }
        return {'size': 0, 'idle': 0, 'active': 0}
    
    async def close(self):
        """Close the pool"""
        if self._pool:
            await self._pool.close()
            self._pool = None

def create_connection_pool(min_size: int = 2, max_size: int = 10, max_queries: int = 50000, max_inactive_connection_lifetime: int = 300):
    """Create database connection pool"""
    return DatabasePool(min_size, max_size, max_queries, max_inactive_connection_lifetime)

async def close_connection_pool(pool: DatabasePool):
    """Close database connection pool"""
    await pool.close()

# Resilient Connection Implementation
async def create_resilient_connection(max_retries: int = 3, retry_delay: float = 1.0):
    """Create connection with retry logic"""
    import asyncio
    
    for attempt in range(max_retries):
        try:
            database_url = get_database_url(async_mode=False)
            if database_url.startswith("postgresql+asyncpg://"):
                database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
            
            connection = await asyncpg.connect(database_url)
            return connection
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                continue
            raise e

# Circuit Breaker Implementation
import time
from typing import Dict, Any

class CircuitBreakerConnection:
    """Circuit breaker pattern for database connections"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def is_available(self) -> bool:
        """Check if circuit breaker allows connections"""
        if self.state == 'CLOSED':
            return True
        elif self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = 'HALF_OPEN'
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def record_success(self):
        """Record successful connection"""
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def record_failure(self):
        """Record failed connection"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'