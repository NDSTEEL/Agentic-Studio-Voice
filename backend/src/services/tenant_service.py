"""
Tenant business logic service
"""
from typing import Optional, Dict, Any
import re

from src.repositories.tenant_repository import TenantRepository
from src.models.tenant import TenantCreateRequest, TenantUpdateRequest


class TenantService:
    """Business logic for tenant management"""
    
    def __init__(self, repository: Optional[TenantRepository] = None):
        self.repository = repository or TenantRepository()
    
    async def create_tenant(self, request: TenantCreateRequest) -> Dict[str, Any]:
        """Create a new tenant with business logic validation"""
        # Validate tenant name
        is_valid = await self.validate_tenant_name(request.name)
        if not is_valid:
            raise ValueError("Invalid tenant name")
        
        # Auto-generate subdomain if not provided
        if not request.subdomain:
            request.subdomain = self._generate_subdomain(request.name)
        
        return await self.repository.create(request)
    
    async def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get tenant by ID"""
        return await self.repository.get_by_id(tenant_id)
    
    async def update_tenant(self, tenant_id: str, request: TenantUpdateRequest) -> Optional[Dict[str, Any]]:
        """Update tenant with business logic validation"""
        if request.name:
            is_valid = await self.validate_tenant_name(request.name)
            if not is_valid:
                raise ValueError("Invalid tenant name")
        
        return await self.repository.update(tenant_id, request)
    
    async def list_tenants(self, page: int = 1, limit: int = 10) -> Dict[str, Any]:
        """List tenants with pagination"""
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 10
            
        return await self.repository.list(page, limit)
    
    async def delete_tenant(self, tenant_id: str) -> bool:
        """Delete tenant"""
        return await self.repository.delete(tenant_id)
    
    async def validate_tenant_name(self, name: str) -> bool:
        """Validate tenant name according to business rules"""
        if not name or len(name.strip()) < 1:
            return False
        
        # Check for valid characters (letters, numbers, spaces, hyphens, underscores)
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', name):
            return False
        
        # Additional business rules can be added here
        return True
    
    def _generate_subdomain(self, name: str) -> str:
        """Generate subdomain from tenant name"""
        # Convert to lowercase, replace spaces and special chars with hyphens
        subdomain = re.sub(r'[^a-zA-Z0-9\-]', '-', name.lower())
        # Remove multiple consecutive hyphens
        subdomain = re.sub(r'-+', '-', subdomain)
        # Remove leading/trailing hyphens
        subdomain = subdomain.strip('-')
        # Truncate if too long
        return subdomain[:50] if len(subdomain) > 50 else subdomain