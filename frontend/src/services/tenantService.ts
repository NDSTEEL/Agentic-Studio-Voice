// TODO: [MOCK_REGISTRY] Mock tenant service - needs real API endpoints
import apiClient from './api'
import { Tenant, CreateTenantRequest, UpdateTenantRequest } from '../types/api'

export const tenantService = {
  // Get all tenants (alias for compatibility)
  async listTenants(): Promise<Tenant[]> {
    return this.getTenants()
  },

  // Get all tenants
  async getTenants(): Promise<Tenant[]> {
    try {
      const response = await apiClient.get<Tenant[]>('/tenants')
      return response.data
    } catch (error) {
      // TODO: [MOCK_REGISTRY] Mock error handling - return empty array for now
      console.warn('Mock: getTenants failed, returning empty array')
      return []
    }
  },

  // Get tenant by ID
  async getTenant(id: string): Promise<Tenant> {
    try {
      const response = await apiClient.get<Tenant>(`/tenants/${id}`)
      return response.data
    } catch (error) {
      // TODO: [MOCK_REGISTRY] Mock tenant data - return placeholder
      console.warn('Mock: getTenant failed, returning mock data')
      return {
        id: id,
        name: 'Mock Tenant',
        status: 'active',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
    }
  },

  // Create new tenant
  async createTenant(tenant: CreateTenantRequest): Promise<Tenant> {
    try {
      const response = await apiClient.post<Tenant>('/tenants', tenant)
      return response.data
    } catch (error) {
      // TODO: [MOCK_REGISTRY] Mock tenant creation - return mock created tenant
      console.warn('Mock: createTenant failed, returning mock created tenant')
      return {
        id: `mock-${Date.now()}`,
        name: tenant.name,
        status: 'active',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
    }
  },

  // Update tenant
  async updateTenant(id: string, tenant: UpdateTenantRequest): Promise<Tenant> {
    try {
      const response = await apiClient.put<Tenant>(`/tenants/${id}`, tenant)
      return response.data
    } catch (error) {
      // TODO: [MOCK_REGISTRY] Mock tenant update - return mock updated tenant
      console.warn('Mock: updateTenant failed, returning mock updated tenant')
      return {
        id: id,
        name: tenant.name || 'Updated Mock Tenant',
        status: tenant.status || 'active',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
    }
  },

  // Delete tenant
  async deleteTenant(id: string): Promise<void> {
    try {
      await apiClient.delete(`/tenants/${id}`)
    } catch (error) {
      // TODO: [MOCK_REGISTRY] Mock tenant deletion - just log for now
      console.warn('Mock: deleteTenant failed, pretending success')
    }
  }
}