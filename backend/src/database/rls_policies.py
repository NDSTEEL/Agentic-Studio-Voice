"""
Row-Level Security (RLS) policies for multi-tenant isolation
Ensures complete tenant data isolation at the database level
"""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from .connection import create_async_db_engine

async def setup_rls_policies(engine: AsyncEngine = None) -> None:
    """
    Set up Row-Level Security policies for all tables
    Ensures tenant isolation at the database level
    """
    if engine is None:
        engine = create_async_db_engine()
    
    async with engine.begin() as conn:
        # Enable RLS on tenants table (self-managing)
        await conn.execute(text("""
            ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
        """))
        
        # Tenants can only see their own record
        await conn.execute(text("""
            CREATE POLICY tenant_isolation ON tenants
            FOR ALL
            TO PUBLIC
            USING (id = current_setting('app.current_tenant_id')::uuid);
        """))
        
        # Enable RLS on voice_agents table
        await conn.execute(text("""
            ALTER TABLE voice_agents ENABLE ROW LEVEL SECURITY;
        """))
        
        # Voice agents are isolated by tenant_id
        await conn.execute(text("""
            CREATE POLICY voice_agent_tenant_isolation ON voice_agents
            FOR ALL
            TO PUBLIC
            USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
        """))
        
        # Enable RLS on knowledge_bases table
        await conn.execute(text("""
            ALTER TABLE knowledge_bases ENABLE ROW LEVEL SECURITY;
        """))
        
        # Knowledge bases are isolated by tenant_id
        await conn.execute(text("""
            CREATE POLICY knowledge_base_tenant_isolation ON knowledge_bases
            FOR ALL
            TO PUBLIC
            USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
        """))

async def set_tenant_context(engine: AsyncEngine, tenant_id: str) -> None:
    """
    Set the current tenant context for RLS
    This should be called at the beginning of each request
    """
    async with engine.begin() as conn:
        await conn.execute(text(f"""
            SET LOCAL app.current_tenant_id = '{tenant_id}';
        """))

async def clear_tenant_context(engine: AsyncEngine) -> None:
    """
    Clear the tenant context (for admin operations)
    """
    async with engine.begin() as conn:
        await conn.execute(text("""
            RESET app.current_tenant_id;
        """))

async def drop_rls_policies(engine: AsyncEngine = None) -> None:
    """
    Drop all RLS policies (for testing or development reset)
    """
    if engine is None:
        engine = create_async_db_engine()
    
    async with engine.begin() as conn:
        # Drop policies first
        await conn.execute(text("DROP POLICY IF EXISTS tenant_isolation ON tenants;"))
        await conn.execute(text("DROP POLICY IF EXISTS voice_agent_tenant_isolation ON voice_agents;"))
        await conn.execute(text("DROP POLICY IF EXISTS knowledge_base_tenant_isolation ON knowledge_bases;"))
        
        # Disable RLS
        await conn.execute(text("ALTER TABLE tenants DISABLE ROW LEVEL SECURITY;"))
        await conn.execute(text("ALTER TABLE voice_agents DISABLE ROW LEVEL SECURITY;"))
        await conn.execute(text("ALTER TABLE knowledge_bases DISABLE ROW LEVEL SECURITY;"))

class TenantContextManager:
    """
    Context manager for handling tenant isolation in database operations
    """
    def __init__(self, engine: AsyncEngine, tenant_id: str):
        self.engine = engine
        self.tenant_id = tenant_id
    
    async def __aenter__(self):
        await set_tenant_context(self.engine, self.tenant_id)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await clear_tenant_context(self.engine)

# Utility function for easier tenant context usage
def with_tenant_context(engine: AsyncEngine, tenant_id: str):
    """
    Create a tenant context manager for database operations
    
    Usage:
        async with with_tenant_context(engine, tenant_id):
            # All database operations here will be tenant-isolated
            result = await session.execute(select(VoiceAgent))
    """
    return TenantContextManager(engine, tenant_id)

if __name__ == "__main__":
    # For testing RLS setup
    async def main():
        engine = create_async_db_engine()
        await setup_rls_policies(engine)
        print("RLS policies set up successfully")
        await engine.dispose()
    
    asyncio.run(main())