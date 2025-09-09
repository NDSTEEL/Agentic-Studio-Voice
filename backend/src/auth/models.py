"""
Authentication data models for user and tenant context
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class UserAuth:
    """User authentication context"""
    user_id: str
    email: str
    tenant_id: str
    roles: Optional[list] = None


@dataclass
class TenantAuth:
    """Tenant authentication context"""
    tenant_id: str
    name: str
    permissions: Optional[list] = None