// TODO: [MOCK_REGISTRY] Mock protected route - needs real authentication check
'use client'
import React, { ReactNode, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import Loading from '../Loading'

interface ProtectedRouteProps {
  children: ReactNode
  fallback?: ReactNode
  redirectTo?: string
}

export default function ProtectedRoute({ 
  children, 
  fallback, 
  redirectTo = '/auth/login' 
}: ProtectedRouteProps) {
  const { isAuthenticated, loading, user } = useAuth()

  useEffect(() => {
    // Redirect to login if not authenticated and not loading
    if (!loading && !isAuthenticated) {
      if (typeof window !== 'undefined') {
        window.location.href = redirectTo
      }
    }
  }, [isAuthenticated, loading, redirectTo])

  // Show loading spinner while checking authentication
  if (loading) {
    return fallback || <Loading size="large" message="Checking authentication..." fullScreen />
  }

  // Show loading if not authenticated (while redirect is happening)
  if (!isAuthenticated || !user) {
    return fallback || <Loading size="large" message="Redirecting..." fullScreen />
  }

  // Render children if authenticated
  return <>{children}</>
}