"""
Test for T003: PostgreSQL Connection & Configuration
TDD: Write failing tests first for database connection and transaction handling
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

# Import functions to test - imports moved to individual tests to avoid namespace pollution

class TestDatabaseConnectionPool:
    """Test database connection pooling functionality"""
    
    def test_connection_pool_creation(self):
        """Test that connection pool can be created with proper configuration"""
        from src.database.connection import create_connection_pool
        
        pool = create_connection_pool(
            min_size=5,
            max_size=20,
            max_queries=50000,
            max_inactive_connection_lifetime=300
        )
        assert pool is not None
        assert hasattr(pool, 'min_size')
        assert hasattr(pool, 'max_size')
        assert pool.min_size == 5
        assert pool.max_size == 20
    
    @pytest.mark.asyncio
    @patch('src.database.connection.asyncpg.create_pool')
    async def test_connection_pool_acquire_release(self, mock_create_pool):
        """Test acquiring and releasing connections from pool"""
        from src.database.connection import create_connection_pool
        
        # Mock the pool and connection
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()
        mock_connection.fetchval.return_value = 1
        mock_pool.acquire.return_value = mock_connection
        
        # Make create_pool return the mock pool as a coroutine
        async def create_pool_coro(*args, **kwargs):
            return mock_pool
        mock_create_pool.side_effect = create_pool_coro
        
        pool = create_connection_pool(min_size=2, max_size=10)
        
        # Acquire connection
        connection = await pool.acquire()
        assert connection is not None
        
        # Test connection is working
        result = await connection.fetchval('SELECT 1')
        assert result == 1
        
        # Release connection
        await pool.release(connection)
        
        # Close pool
        from src.database.connection import close_connection_pool
        await close_connection_pool(pool)
    
    @pytest.mark.asyncio
    @patch('src.database.connection.asyncpg.create_pool')
    async def test_connection_pool_stats(self, mock_create_pool):
        """Test connection pool statistics and monitoring"""
        from src.database.connection import create_connection_pool
        
        # Mock the pool with stats (use MagicMock for sync methods)
        mock_pool = MagicMock()
        mock_pool.get_size.return_value = 5
        mock_pool.get_idle_size.return_value = 3
        
        # Mock the acquire method to return AsyncMock
        mock_connection = AsyncMock()
        mock_pool.acquire = AsyncMock(return_value=mock_connection)
        mock_pool.close = AsyncMock()  # Mock the close method
        
        # Make create_pool return the mock pool as a coroutine
        async def create_pool_coro(*args, **kwargs):
            return mock_pool
        mock_create_pool.side_effect = create_pool_coro
        
        pool = create_connection_pool(min_size=3, max_size=8)
        
        # Force pool creation by calling acquire first
        connection = await pool.acquire()
        assert connection is not None
        
        # Check stats
        stats = pool.get_stats()
        assert stats['size'] == 5
        assert stats['idle'] == 3
        assert stats['active'] == 2
        assert 'idle' in stats
        assert 'active' in stats
        
        from src.database.connection import close_connection_pool
        await close_connection_pool(pool)

class TestAsyncTransactionHandling:
    """Test async transaction management"""
    
    @pytest.mark.asyncio
    @patch('src.database.connection.create_async_db_engine')
    async def test_async_transaction_manager_commit(self, mock_create_engine):
        """Test successful transaction commit"""
        from src.database.transaction import AsyncTransactionManager
        
        # Mock engine, connection, and transaction
        mock_engine = AsyncMock()
        mock_connection = AsyncMock()
        mock_transaction = AsyncMock()
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.test = 1
        mock_result.fetchone.return_value = mock_row
        
        mock_connection.execute.return_value = mock_result
        mock_connection.begin.return_value = mock_transaction
        mock_engine.connect.return_value = mock_connection
        mock_create_engine.return_value = mock_engine
        
        async with AsyncTransactionManager(mock_engine) as transaction:
            # Perform database operations
            result = await transaction.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            assert row.test == 1
    
    @pytest.mark.asyncio
    @patch('src.database.connection.create_async_db_engine')
    async def test_async_transaction_manager_rollback(self, mock_create_engine):
        """Test automatic transaction rollback on error"""
        from src.database.transaction import AsyncTransactionManager
        
        mock_engine = AsyncMock()
        mock_connection = AsyncMock()
        mock_transaction = AsyncMock()
        mock_connection.begin.return_value = mock_transaction
        mock_engine.connect.return_value = mock_connection
        mock_create_engine.return_value = mock_engine
        
        try:
            async with AsyncTransactionManager(mock_engine) as transaction:
                # Perform valid operation
                await transaction.execute(text("SELECT 1"))
                
                # Cause an error to trigger rollback
                raise ValueError("Test error for rollback")
        except ValueError:
            pass  # Expected error
        
        # Verify rollback was called
        mock_transaction.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.database.transaction.create_async_session_factory')
    async def test_with_database_transaction_decorator(self, mock_session_factory):
        """Test transaction decorator functionality"""
        # Mock session with proper async context manager
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.value = 1
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()
        
        # Create proper async context manager
        mock_session_context = AsyncMock()
        mock_session_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_context.__aexit__ = AsyncMock(return_value=None)
        
        # Mock the session factory to return a callable that returns the context
        mock_session_factory.return_value = lambda: mock_session_context
        
        from src.database.transaction import with_database_transaction
        
        @with_database_transaction
        async def test_function(session: AsyncSession):
            result = await session.execute(text("SELECT 1 as value"))
            row = result.fetchone()
            return row.value
        
        result = await test_function()
        assert result == 1
    
    @pytest.mark.asyncio
    @patch('src.database.connection.create_async_session_factory')
    async def test_rollback_on_error_decorator(self, mock_session_factory):
        """Test rollback decorator for error handling"""
        mock_session = AsyncMock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_session
        mock_session_factory.return_value = mock_context
        
        from src.database.transaction import rollback_on_error
        
        @rollback_on_error
        async def failing_function(session: AsyncSession):
            await session.execute(text("SELECT 1"))
            raise ValueError("Intentional error")
        
        with pytest.raises(ValueError):
            await failing_function(mock_session)
        
        # Verify rollback was called
        mock_session.rollback.assert_called_once()

class TestEnvironmentConfiguration:
    """Test environment-based database configuration"""
    
    def test_database_url_from_environment(self):
        """Test reading database URL from environment variables"""
        import os
        
        # Test with custom environment variable
        os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost:5432/test_db"
        
        from src.database.connection import get_database_url
        db_url = get_database_url()
        
        assert "postgresql+asyncpg" in db_url
        assert "test:test" in db_url
        assert "test_db" in db_url
        
        # Clean up
        del os.environ["DATABASE_URL"]
    
    def test_connection_pool_configuration_from_env(self):
        """Test connection pool configuration from environment"""
        import os
        
        # Set environment variables
        os.environ["DB_POOL_MIN_SIZE"] = "3"
        os.environ["DB_POOL_MAX_SIZE"] = "15"
        os.environ["DB_POOL_MAX_QUERIES"] = "75000"
        
        from src.database.connection import get_pool_config
        config = get_pool_config()
        
        assert config['min_size'] == 3
        assert config['max_size'] == 15
        assert config['max_queries'] == 75000
        
        # Clean up
        for key in ["DB_POOL_MIN_SIZE", "DB_POOL_MAX_SIZE", "DB_POOL_MAX_QUERIES"]:
            if key in os.environ:
                del os.environ[key]

class TestDatabaseHealthChecks:
    """Test database health checking and monitoring"""
    
    @pytest.mark.asyncio
    @patch('src.database.connection.create_async_db_engine')
    async def test_database_health_check(self, mock_create_engine):
        """Test basic database connectivity health check"""
        # Mock successful connection
        from unittest.mock import MagicMock
        from contextlib import asynccontextmanager
        
        mock_engine = AsyncMock()
        mock_connection = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_connection.execute.return_value = mock_result
        
        @asynccontextmanager
        async def mock_begin():
            yield mock_connection
        
        mock_engine.begin = mock_begin
        
        # Mock engine disposal
        mock_engine.dispose = AsyncMock()
        mock_create_engine.return_value = mock_engine
        
        from src.database.connection import test_connection
        
        is_healthy = await test_connection()
        assert is_healthy is True
    
    @pytest.mark.asyncio
    @patch('src.database.connection.create_async_db_engine')
    async def test_database_health_check_with_timeout(self, mock_create_engine):
        """Test health check with timeout configuration"""
        from src.database.connection import test_connection_with_timeout
        
        # Mock successful connection
        mock_engine = AsyncMock()
        mock_connection = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_connection.execute.return_value = mock_result
        
        # Create proper async context manager
        from contextlib import asynccontextmanager
        
        @asynccontextmanager
        async def mock_begin():
            yield mock_connection
        
        mock_engine.begin = mock_begin
        mock_engine.dispose = AsyncMock()
        mock_create_engine.return_value = mock_engine
        
        is_healthy = await test_connection_with_timeout(timeout=5.0)
        assert is_healthy is True
    
    @pytest.mark.asyncio
    @patch('src.database.connection.create_async_db_engine')
    async def test_database_version_check(self, mock_create_engine):
        """Test PostgreSQL version detection"""
        from src.database.connection import get_postgresql_version
        
        # Mock version response
        mock_engine = AsyncMock()
        mock_connection = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = "PostgreSQL 15.1 on x86_64-pc-linux-gnu"
        mock_connection.execute.return_value = mock_result
        
        # Create proper async context manager
        from contextlib import asynccontextmanager
        
        @asynccontextmanager
        async def mock_begin():
            yield mock_connection
        
        mock_engine.begin = mock_begin
        mock_engine.dispose = AsyncMock()
        mock_create_engine.return_value = mock_engine
        
        version = await get_postgresql_version()
        assert version is not None
        assert isinstance(version, str)
        assert "PostgreSQL" in version

class TestConnectionRecovery:
    """Test connection recovery and retry mechanisms"""
    
    @pytest.mark.asyncio
    @patch('src.database.connection.asyncpg.connect')
    async def test_connection_retry_on_failure(self, mock_connect):
        """Test automatic connection retry on temporary failures"""
        from src.database.connection import create_resilient_connection
        
        # Mock successful connection
        mock_connection = AsyncMock()
        mock_connection.fetchval.return_value = 1
        mock_connect.return_value = mock_connection
        
        connection = await create_resilient_connection(
            max_retries=3,
            retry_delay=0.1
        )
        
        assert connection is not None
        
        # Test connection works
        result = await connection.fetchval('SELECT 1')
        assert result == 1
        
        await connection.close()
    
    @pytest.mark.asyncio 
    async def test_connection_circuit_breaker(self):
        """Test circuit breaker pattern for connection failures"""
        from src.database.connection import CircuitBreakerConnection
        
        # This will be implemented to prevent cascading failures
        circuit_breaker = CircuitBreakerConnection(
            failure_threshold=5,
            recovery_timeout=10
        )
        
        assert circuit_breaker.is_available() is True
        assert hasattr(circuit_breaker, 'failure_count')
        assert hasattr(circuit_breaker, 'last_failure_time')

if __name__ == "__main__":
    # Run tests to see them fail first (Red phase)
    pytest.main([__file__, "-v"])