import { createContext, useContext, useState, useCallback, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import {
  exchangePortalCode,
  getCurrentSession,
  login as authLogin,
  logout as authLogout,
} from '../services/authService'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [auth, setAuth] = useState({ user: null, role: null })
  const [ready, setReady] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    let cancelled = false
    const bootstrap = async () => {
      try {
        const params = new URLSearchParams(window.location.search)
        const state = params.get('state')
        const code = params.get('code')
        const result = state && code
          ? await exchangePortalCode(state, code)
          : await getCurrentSession()
        if (state && code) {
          params.delete('state')
          params.delete('code')
          const query = params.toString()
          window.history.replaceState({}, '', `${window.location.pathname}${query ? `?${query}` : ''}`)
        }
        if (!cancelled && result?.user) setAuth({ user: result.user, role: result.user.role })
      } catch {
        if (!cancelled) setAuth({ user: null, role: null })
      } finally {
        if (!cancelled) setReady(true)
      }
    }
    void bootstrap()
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    const sessionExpired = () => {
      setAuth({ user: null, role: null })
      setReady(true)
      navigate('/login', { replace: true })
    }
    window.addEventListener('docmind:session-expired', sessionExpired)
    return () => window.removeEventListener('docmind:session-expired', sessionExpired)
  }, [navigate])

  const login = useCallback(async (username, password) => {
    const result = await authLogin(username, password)
    setAuth({ user: result.user, role: result.user.role })
    toast.success(result.welcomeMessage ?? `Welcome back, ${result.user.name || result.user.username}!`, {
      description: `Signed in as ${result.user.role}`,
    })
    return result.redirect
  }, [])

  const logout = useCallback(async () => {
    try {
      await authLogout()
      setAuth({ user: null, role: null })
      navigate('/login', { replace: true })
      toast('Signed out successfully')
    } catch (error) {
      toast.error(error.message || 'Sign-out did not complete. Please try again.')
    }
  }, [navigate])

  const value = useMemo(() => ({
    user: auth.user,
    role: auth.role,
    ready,
    isAuthenticated: !!auth.user,
    login,
    logout,
  }), [auth, ready, login, logout])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export default function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside <AuthProvider>')
  return context
}
