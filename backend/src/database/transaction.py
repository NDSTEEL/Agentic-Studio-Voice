"""
Async transaction management utilities for database operations
"""
import asyncio
from contextlib import asynccontextmanager
from functools import wraps
from typing import AsyncGenerator, Callable, Any
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy import text

from .connection import create_async_db_engine, create_async_session_factory

class AsyncTransactionManager:
    """Context manager for async database transactions"""
    
    def __init__(self, engine: AsyncEngine = None):
        self.engine = engine or create_async_db_engine()
        self.connection = None
        self.transaction = None
    
    async def __aenter__(self):
        """Enter transaction context"""
        self.connection = await self.engine.connect()
        self.transaction = await self.connection.begin()
        return self.connection
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit transaction context with commit/rollback"""
        try:
            if exc_type is None:
                # No exception, commit the transaction
                await self.transaction.commit()
            else:
                # Exception occurred, rollback
                await self.transaction.rollback()
        finally:
            # Always close the connection
            await self.connection.close()

def with_database_transaction(func: Callable) -> Callable:
    """Decorator to wrap function in database transaction"""
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        session_factory = create_async_session_factory()
        async with session_factory() as session:
            try:
                result = await func(session, *args, **kwargs)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    return wrapper

def rollback_on_error(func: Callable) -> Callable:
    """Decorator to automatically rollback session on errors"""
    
    @wraps(func)
    async def wrapper(session: AsyncSession, *args, **kwargs):
        try:
            result = await func(session, *args, **kwargs)
            return result
        except Exception as e:
            await session.rollback()
            raise e
    
    return wrapper

@asynccontextmanager
async def get_transaction(engine: AsyncEngine = None) -> AsyncGenerator[Any, None]:
    """Context manager for manual transaction control"""
    engine = engine or create_async_db_engine()
    
    async with AsyncTransactionManager(engine) as connection:
        yield connection

class TransactionScope:
    """Transaction scope manager for nested transactions"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.savepoint = None
    
    async def __aenter__(self):
        """Create savepoint for nested transaction"""
        self.savepoint = await self.session.begin_nested()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Commit or rollback savepoint"""
        if exc_type is None:
            await self.savepoint.commit()
        else:
            await self.savepoint.rollback()

async def execute_in_transaction(query: str, params: dict = None, engine: AsyncEngine = None):
    """Execute a query within a transaction"""
    engine = engine or create_async_db_engine()
    
    async with AsyncTransactionManager(engine) as connection:
        if params:
            result = await connection.execute(text(query), params)
        else:
            result = await connection.execute(text(query))
        return result

async def bulk_insert_in_transaction(table_name: str, data: list, engine: AsyncEngine = None):
    """Perform bulk insert within a transaction"""
    if not data:
        return
    
    engine = engine or create_async_db_engine()
    
    # Build bulk insert query
    columns = list(data[0].keys())
    placeholders = ', '.join([f':{col}' for col in columns])
    query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
    
    async with AsyncTransactionManager(engine) as connection:
        await connection.execute(text(query), data)

class BatchProcessor:
    """Process operations in batches within transactions"""
    
    def __init__(self, batch_size: int = 1000, engine: AsyncEngine = None):
        self.batch_size = batch_size
        self.engine = engine or create_async_db_engine()
    
    async def process_batches(self, data: list, processor_func: Callable):
        """Process data in batches"""
        for i in range(0, len(data), self.batch_size):
            batch = data[i:i + self.batch_size]
            
            async with AsyncTransactionManager(self.engine) as connection:
                await processor_func(connection, batch)

# Transaction monitoring and metrics
class TransactionMetrics:
    """Monitor transaction performance and statistics"""
    
    def __init__(self):
        self.transaction_count = 0
        self.commit_count = 0
        self.rollback_count = 0
        self.total_duration = 0.0
    
    def record_transaction(self, duration: float, committed: bool):
        """Record transaction metrics"""
        self.transaction_count += 1
        self.total_duration += duration
        
        if committed:
            self.commit_count += 1
        else:
            self.rollback_count += 1
    
    def get_stats(self) -> dict:
        """Get transaction statistics"""
        avg_duration = self.total_duration / max(self.transaction_count, 1)
        commit_rate = self.commit_count / max(self.transaction_count, 1) * 100
        
        return {
            'total_transactions': self.transaction_count,
            'commits': self.commit_count,
            'rollbacks': self.rollback_count,
            'average_duration_ms': avg_duration * 1000,
            'commit_rate_percent': commit_rate
        }

# Global metrics instance
transaction_metrics = TransactionMetrics()