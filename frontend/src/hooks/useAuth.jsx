import { createContext, useContext, useState, useCallback, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import {
  login as authLogin,
  logout as authLogout,
} from '../services/authService'

const AUTH_TOKEN_KEY = 'auth_token'
const AUTH_USER_KEY = 'auth_user'

function clearAllAuthStorage() {
  try {
    localStorage.removeItem(AUTH_TOKEN_KEY)
    localStorage.removeItem(AUTH_USER_KEY)
  } catch {
    /* swallow */
  }
}

/** Portal-demo SSO: token passed via ?sso= on redirect from sso-bridge.html */
function readSsoFromUrl() {
  try {
    const params = new URLSearchParams(window.location.search)
    const sso = params.get('sso')
    if (!sso) return null

    const payload = JSON.parse(decodeURIComponent(sso))
    if (!payload?.token || !payload?.user) return null

    params.delete('sso')
    const qs = params.toString()
    const clean = qs
      ? `${window.location.pathname}?${qs}`
      : window.location.pathname
    window.history.replaceState({}, '', clean)

    return { token: payload.token, user: payload.user, role: payload.user.role }
  } catch {
    return null
  }
}

function readStoredAuth() {
  const ssoAuth = readSsoFromUrl()
  if (ssoAuth) {
    try {
      localStorage.setItem(AUTH_TOKEN_KEY, ssoAuth.token)
      localStorage.setItem(AUTH_USER_KEY, JSON.stringify(ssoAuth.user))
    } catch {
      /* swallow */
    }
    return ssoAuth
  }

  try {
    const token = localStorage.getItem(AUTH_TOKEN_KEY)
    const raw = localStorage.getItem(AUTH_USER_KEY)
    if (token && raw) {
      const user = JSON.parse(raw)
      return { token, user, role: user.role }
    }
  } catch {
    /* corrupted — treat as logged-out */
  }
  return { token: null, user: null, role: null }
}

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [auth, setAuth] = useState(readStoredAuth)
  const navigate = useNavigate()

  const completeLogin = useCallback(({ token, user, redirect, welcomeMessage }) => {
    clearAllAuthStorage()
    localStorage.setItem(AUTH_TOKEN_KEY, token)
    localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user))
    setAuth({ token, user, role: user.role })
    toast.success(welcomeMessage ?? `Welcome back, ${user.name || user.username}!`, {
      description: `Signed in as ${user.role}`,
    })
    return redirect
  }, [])

  const login = useCallback(
    async (username, password) => {
      const result = await authLogin(username, password)
      return completeLogin(result)
    },
    [completeLogin],
  )

  const logout = useCallback(() => {
    authLogout()
    clearAllAuthStorage()
    setAuth({ token: null, user: null, role: null })
    navigate('/login', { replace: true })
    toast('Signed out successfully')
  }, [navigate])

  const value = useMemo(
    () => ({
      user: auth.user,
      token: auth.token,
      role: auth.role,
      isAuthenticated: !!auth.token,
      login,
      logout,
    }),
    [auth, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export default function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
