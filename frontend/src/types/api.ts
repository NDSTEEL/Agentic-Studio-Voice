// API response types
export interface Tenant {
  id: string
  name: string
  status: 'active' | 'inactive' | 'suspended'
  created_at: string
  updated_at: string
}

export interface CreateTenantRequest {
  name: string
  status?: 'active' | 'inactive' | 'suspended'
}

export interface UpdateTenantRequest {
  name?: string
  status?: 'active' | 'inactive' | 'suspended'
}

export interface ApiError {
  message: string
  code?: string
  details?: any
}

export interface ApiResponse<T> {
  data: T
  message?: string
  success: boolean
}