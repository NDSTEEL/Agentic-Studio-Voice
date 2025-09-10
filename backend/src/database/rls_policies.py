"""
Row Level Security (RLS) Policies
PostgreSQL RLS policies for multi-tenant data isolation
"""
from sqlalchemy import text


def setup_rls_policies(engine):
    """
    Set up Row Level Security policies for multi-tenant isolation
    
    This function creates RLS policies that ensure:
    1. Users can only access data from their tenant
    2. All queries are automatically filtered by tenant_id
    3. INSERT/UPDATE operations must include valid tenant_id
    """
    
    # RLS policies SQL statements
    rls_policies = [
        # Enable RLS on tenants table
        "ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;",
        
        # Enable RLS on voice_agents table
        "ALTER TABLE voice_agents ENABLE ROW LEVEL SECURITY;",
        
        # Enable RLS on knowledge_bases table
        "ALTER TABLE knowledge_bases ENABLE ROW LEVEL SECURITY;",
        
        # Tenant isolation policy for voice_agents
        """
        CREATE POLICY tenant_isolation_voice_agents ON voice_agents
        USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
        """,
        
        # Tenant isolation policy for knowledge_bases
        """
        CREATE POLICY tenant_isolation_knowledge_bases ON knowledge_bases
        USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
        """,
        
        # Tenant self-access policy (tenants can see their own record)
        """
        CREATE POLICY tenant_self_access ON tenants
        USING (id = current_setting('app.current_tenant_id')::uuid);
        """
    ]
    
    # Execute RLS policies
    with engine.connect() as conn:
        for policy_sql in rls_policies:
            try:
                conn.execute(text(policy_sql))
                conn.commit()
            except Exception as e:
                # Policy might already exist, continue
                print(f"RLS Policy note: {e}")
                continue
    
    return True


def set_tenant_context(engine, tenant_id: str):
    """
    Set the current tenant context for RLS policies
    """
    with engine.connect() as conn:
        conn.execute(text(f"SET app.current_tenant_id = '{tenant_id}'"))
        conn.commit()


def clear_tenant_context(engine):
    """
    Clear the current tenant context
    """
    with engine.connect() as conn:
        conn.execute(text("RESET app.current_tenant_id"))
        conn.commit()


def create_tenant_aware_session(engine, tenant_id: str):
    """
    Create a database session with tenant context set
    """
    from sqlalchemy.orm import sessionmaker
    
    # Set tenant context
    set_tenant_context(engine, tenant_id)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()