import { useCallback, useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { getStudentAccess } from '../services/systemAccessService'

const POLL_MS = 60_000

/**
 * Loads student-access policy for gating. Polls and refetches on window focus.
 */
export function useStudentAccessGate() {
  const location = useLocation()
  const [state, setState] = useState({
    loading: true,
    enabled: true,
    message: '',
    updatedAt: null,
  })

  const refresh = useCallback(async () => {
    try {
      const data = await getStudentAccess()
      setState({
        loading: false,
        enabled: data.enabled,
        message: data.message || '',
        updatedAt: data.updatedAt,
      })
    } catch {
      setState((s) => ({ ...s, loading: false, enabled: true }))
    }
  }, [])

  useEffect(() => {
    // Initial fetch — intentionally triggers setState from an async effect.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh()
  }, [refresh])

  useEffect(() => {
    const id = window.setInterval(refresh, POLL_MS)
    return () => window.clearInterval(id)
  }, [refresh])

  useEffect(() => {
    const onFocus = () => {
      refresh()
    }
    window.addEventListener('focus', onFocus)
    return () => window.removeEventListener('focus', onFocus)
  }, [refresh])

  const onUnavailableRoute = location.pathname === '/student-unavailable'

  return {
    ...state,
    onUnavailableRoute,
    refresh,
  }
}
