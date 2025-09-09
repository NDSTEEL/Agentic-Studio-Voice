// TODO: [MOCK_REGISTRY] Mock API constants - needs environment configuration
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000'
export const API_TIMEOUT = 10000
export const API_VERSION = 'v1'

// API Endpoints
export const API_ENDPOINTS = {
  TENANTS: '/tenants',
  USERS: '/users',
  AUTH: '/auth',
} as const

// HTTP Status Codes
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  INTERNAL_SERVER_ERROR: 500,
} as const