"""
Tenant management API endpoints
"""
from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional

from src.models.tenant import (
    TenantCreateRequest, 
    TenantUpdateRequest, 
    TenantResponse, 
    TenantListResponse
)
from src.services.tenant_service import TenantService


router = APIRouter()


@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(request: TenantCreateRequest):
    """
    Create new tenant
    """
    service = TenantService()
    try:
        tenant_data = await service.create_tenant(request)
        return TenantResponse(**tenant_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(tenant_id: str):
    """
    Get tenant details by ID
    """
    service = TenantService()
    tenant_data = await service.get_tenant(tenant_id)
    
    if not tenant_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    
    return TenantResponse(**tenant_data)


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(tenant_id: str, request: TenantUpdateRequest):
    """
    Update tenant details
    """
    service = TenantService()
    try:
        tenant_data = await service.update_tenant(tenant_id, request)
        
        if not tenant_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        
        return TenantResponse(**tenant_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/", response_model=TenantListResponse)
async def list_tenants(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page")
):
    """
    List tenants with pagination
    """
    service = TenantService()
    try:
        tenant_data = await service.list_tenants(page=page, limit=limit)
        return TenantListResponse(**tenant_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(tenant_id: str):
    """
    Delete tenant
    """
    service = TenantService()
    deleted = await service.delete_tenant(tenant_id)
    
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")