// TODO: [MOCK_REGISTRY] Mock token storage - needs secure storage implementation
const TOKEN_KEY = 'auth_token'
const TOKEN_EXPIRY_KEY = 'auth_token_expiry'

export function setToken(token: string, expiresIn?: number): void {
  if (typeof window === 'undefined') {
    return // SSR safety
  }

  try {
    localStorage.setItem(TOKEN_KEY, token)
    
    if (expiresIn) {
      const expiry = Date.now() + (expiresIn * 1000)
      localStorage.setItem(TOKEN_EXPIRY_KEY, expiry.toString())
    }
  } catch (error) {
    console.error('Failed to store authentication token:', error)
  }
}

export function getToken(): string | null {
  if (typeof window === 'undefined') {
    return null // SSR safety
  }

  try {
    const token = localStorage.getItem(TOKEN_KEY)
    
    if (!token) {
      return null
    }

    // Check if token has expired
    const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY)
    if (expiry && Date.now() > parseInt(expiry)) {
      // Token has expired, remove it
      removeToken()
      return null
    }

    return token
  } catch (error) {
    console.error('Failed to retrieve authentication token:', error)
    return null
  }
}

export function removeToken(): void {
  if (typeof window === 'undefined') {
    return // SSR safety
  }

  try {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(TOKEN_EXPIRY_KEY)
  } catch (error) {
    console.error('Failed to remove authentication token:', error)
  }
}

export function isTokenExpired(): boolean {
  if (typeof window === 'undefined') {
    return true
  }

  const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY)
  if (!expiry) {
    return false // No expiry set, assume token is valid
  }

  return Date.now() > parseInt(expiry)
}

export function storeToken(token: string): void {
  setToken(token)
}

export function retrieveToken(): string | null {
  return getToken()
}

export function clearToken(): void {
  removeToken()
}