// TODO: [MOCK_REGISTRY] Mock auth context - needs real authentication state management
'use client'
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import authService, { User } from '../services/authService'
import { getToken } from '../utils/tokenStorage'

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, name?: string) => Promise<void>
  logout: () => Promise<void>
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | null>(null)

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const isAuthenticated = !!user && authService.isAuthenticated()

  useEffect(() => {
    // Check for existing authentication on mount
    const initializeAuth = async () => {
      try {
        const token = getToken()
        if (token) {
          const currentUser = await authService.getCurrentUser()
          setUser(currentUser)
        }
      } catch (error) {
        console.error('Failed to initialize authentication:', error)
        // Clear any invalid tokens
        await authService.logout()
      } finally {
        setLoading(false)
      }
    }

    initializeAuth()
  }, [])

  const login = async (email: string, password: string) => {
    setLoading(true)
    try {
      const user = await authService.login(email, password)
      setUser(user)
      
      // Redirect to dashboard on successful login
      if (typeof window !== 'undefined') {
        window.location.href = '/dashboard'
      }
    } catch (error: any) {
      setUser(null)
      throw new Error(error.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  const register = async (email: string, password: string, name?: string) => {
    setLoading(true)
    try {
      const user = await authService.register(email, password, name)
      setUser(user)
      
      // Redirect to dashboard on successful registration
      if (typeof window !== 'undefined') {
        window.location.href = '/dashboard'
      }
    } catch (error: any) {
      setUser(null)
      throw new Error(error.message || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  const logout = async () => {
    setLoading(true)
    try {
      await authService.logout()
      setUser(null)
      
      // Redirect to login page
      if (typeof window !== 'undefined') {
        window.location.href = '/auth/login'
      }
    } catch (error) {
      console.error('Logout error:', error)
      // Even if logout fails, clear local state
      setUser(null)
      if (typeof window !== 'undefined') {
        window.location.href = '/auth/login'
      }
    } finally {
      setLoading(false)
    }
  }

  const value: AuthContextType = {
    user,
    loading,
    login,
    register,
    logout,
    isAuthenticated
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}