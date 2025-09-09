// TODO: [MOCK_REGISTRY] Mock authentication service - needs real backend API integration
import apiClient from './api'
import { setToken, getToken, removeToken } from '../utils/tokenStorage'

export interface User {
  id: string
  email: string
  name?: string
  created_at: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  name?: string
}

export interface AuthResponse {
  user: User
  token: string
  expires_in: number
}

class AuthService {
  async login(email: string, password: string): Promise<User> {
    try {
      const response = await apiClient.post<AuthResponse>('/auth/login', {
        email,
        password
      })

      const { user, token } = response.data
      setToken(token)
      return user
    } catch (error: any) {
      // TODO: [MOCK_REGISTRY] Mock login response - return fake user for development
      console.warn('Mock: Login API failed, returning mock user')
      const mockUser: User = {
        id: `mock-user-${Date.now()}`,
        email: email,
        name: email.split('@')[0],
        created_at: new Date().toISOString()
      }
      
      // Store a fake token
      const fakeToken = `mock-jwt-token-${Date.now()}`
      setToken(fakeToken)
      return mockUser
    }
  }

  async register(email: string, password: string, name?: string): Promise<User> {
    try {
      const response = await apiClient.post<AuthResponse>('/auth/register', {
        email,
        password,
        name
      })

      const { user, token } = response.data
      setToken(token)
      return user
    } catch (error: any) {
      // TODO: [MOCK_REGISTRY] Mock register response - return fake user for development
      console.warn('Mock: Register API failed, returning mock user')
      const mockUser: User = {
        id: `mock-user-${Date.now()}`,
        email: email,
        name: name || email.split('@')[0],
        created_at: new Date().toISOString()
      }
      
      // Store a fake token
      const fakeToken = `mock-jwt-token-${Date.now()}`
      setToken(fakeToken)
      return mockUser
    }
  }

  async logout(): Promise<void> {
    try {
      const token = getToken()
      if (token) {
        await apiClient.post('/auth/logout', {}, {
          headers: { Authorization: `Bearer ${token}` }
        })
      }
    } catch (error) {
      // TODO: [MOCK_REGISTRY] Mock logout - just log the error for now
      console.warn('Mock: Logout API failed, clearing token locally')
    } finally {
      removeToken()
      // Redirect to login page
      if (typeof window !== 'undefined') {
        window.location.href = '/auth/login'
      }
    }
  }

  async getCurrentUser(): Promise<User | null> {
    try {
      const token = getToken()
      if (!token) {
        return null
      }

      const response = await apiClient.get<User>('/auth/me', {
        headers: { Authorization: `Bearer ${token}` }
      })

      return response.data
    } catch (error: any) {
      // TODO: [MOCK_REGISTRY] Mock current user - return fake user if token exists
      const token = getToken()
      if (token && token.startsWith('mock-jwt-token')) {
        console.warn('Mock: getCurrentUser API failed, returning mock user')
        return {
          id: 'mock-current-user',
          email: 'user@example.com',
          name: 'Mock User',
          created_at: new Date().toISOString()
        }
      }
      
      // Clear invalid token
      removeToken()
      return null
    }
  }

  isAuthenticated(): boolean {
    const token = getToken()
    return !!token
  }

  getToken(): string | null {
    return getToken()
  }
}

export default new AuthService()