"""
Tenant repository for database operations
"""
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from datetime import datetime

from src.models.tenant import Tenant, TenantCreateRequest, TenantUpdateRequest
from src.database.connection import get_async_session


class TenantRepository:
    """Repository for tenant database operations"""
    
    async def create(self, request: TenantCreateRequest) -> Dict[str, Any]:
        """Create a new tenant"""
        async with get_async_session() as session:
            tenant = Tenant(
                name=request.name,
                subdomain=request.subdomain
            )
            
            session.add(tenant)
            await session.commit()
            await session.refresh(tenant)
            
            return {
                "id": tenant.id,
                "name": tenant.name,
                "status": tenant.status,
                "subdomain": tenant.subdomain,
                "created_at": tenant.created_at.isoformat() if tenant.created_at else None,
                "updated_at": tenant.updated_at.isoformat() if tenant.updated_at else None
            }
    
    async def get_by_id(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get tenant by ID"""
        async with get_async_session() as session:
            stmt = select(Tenant).where(Tenant.id == tenant_id)
            result = await session.execute(stmt)
            tenant = result.scalar_one_or_none()
            
            if not tenant:
                return None
            
            return {
                "id": tenant.id,
                "name": tenant.name,
                "status": tenant.status,
                "subdomain": tenant.subdomain,
                "created_at": tenant.created_at.isoformat() if tenant.created_at else None,
                "updated_at": tenant.updated_at.isoformat() if tenant.updated_at else None
            }
    
    async def update(self, tenant_id: str, request: TenantUpdateRequest) -> Optional[Dict[str, Any]]:
        """Update tenant data"""
        async with get_async_session() as session:
            # Prepare update data
            update_data = {}
            if request.name is not None:
                update_data['name'] = request.name
            if request.status is not None:
                update_data['status'] = request.status
            if request.subdomain is not None:
                update_data['subdomain'] = request.subdomain
            
            if update_data:
                update_data['updated_at'] = datetime.utcnow()
            
            stmt = (
                update(Tenant)
                .where(Tenant.id == tenant_id)
                .values(**update_data)
                .returning(Tenant)
            )
            
            result = await session.execute(stmt)
            tenant = result.scalar_one_or_none()
            
            if not tenant:
                return None
            
            await session.commit()
            
            return {
                "id": tenant.id,
                "name": tenant.name,
                "status": tenant.status,
                "subdomain": tenant.subdomain,
                "created_at": tenant.created_at.isoformat() if tenant.created_at else None,
                "updated_at": tenant.updated_at.isoformat() if tenant.updated_at else None
            }
    
    async def list(self, page: int = 1, limit: int = 10) -> Dict[str, Any]:
        """List tenants with pagination"""
        async with get_async_session() as session:
            # Calculate offset
            offset = (page - 1) * limit
            
            # Get total count
            count_stmt = select(func.count(Tenant.id))
            count_result = await session.execute(count_stmt)
            total = count_result.scalar()
            
            # Get tenants
            stmt = (
                select(Tenant)
                .offset(offset)
                .limit(limit)
                .order_by(Tenant.created_at.desc())
            )
            
            result = await session.execute(stmt)
            tenants = result.scalars().all()
            
            tenant_list = []
            for tenant in tenants:
                tenant_list.append({
                    "id": tenant.id,
                    "name": tenant.name,
                    "status": tenant.status,
                    "subdomain": tenant.subdomain,
                    "created_at": tenant.created_at.isoformat() if tenant.created_at else None,
                    "updated_at": tenant.updated_at.isoformat() if tenant.updated_at else None
                })
            
            return {
                "tenants": tenant_list,
                "total": total,
                "page": page,
                "limit": limit
            }
    
    async def delete(self, tenant_id: str) -> bool:
        """Delete tenant by ID"""
        async with get_async_session() as session:
            stmt = delete(Tenant).where(Tenant.id == tenant_id)
            result = await session.execute(stmt)
            await session.commit()
            
            return result.rowcount > 0