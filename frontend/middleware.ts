// TODO: [MOCK_REGISTRY] Mock Next.js middleware - needs real JWT verification
import { NextRequest, NextResponse } from 'next/server'

// Define protected routes that require authentication
const protectedPaths = [
  '/dashboard',
  '/tenants',
  '/settings',
  '/api/protected'
]

// Define public routes that don't require authentication
const publicPaths = [
  '/auth/login',
  '/auth/register',
  '/',
  '/api/auth'
]

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  const authToken = request.cookies.get('auth_token') || request.headers.get('authorization')

  // Allow public paths without authentication
  if (publicPaths.some(path => pathname.startsWith(path))) {
    return NextResponse.next()
  }

  // Check if path requires authentication
  const isProtectedRoute = protectedPaths.some(path => pathname.startsWith(path))
  
  if (isProtectedRoute) {
    // TODO: [MOCK_REGISTRY] Mock JWT verification - should verify token with backend
    if (!authToken) {
      // Redirect to login for protected routes without token
      const loginUrl = new URL('/auth/login', request.url)
      loginUrl.searchParams.set('redirect', pathname)
      return NextResponse.redirect(loginUrl)
    }

    // Mock token validation - in production, verify with backend
    const token = authToken.value || authToken.toString().replace('Bearer ', '')
    if (token.startsWith('mock-jwt-token') || token.length > 10) {
      // Allow mock tokens and assume valid tokens are longer than 10 chars
      return NextResponse.next()
    } else {
      // Invalid token, redirect to login
      const loginUrl = new URL('/auth/login', request.url)
      return NextResponse.redirect(loginUrl)
    }
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    // Match all paths except static files and API routes
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ]
}