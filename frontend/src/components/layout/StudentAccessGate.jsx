import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useStudentAccessGate } from '../../hooks/useStudentAccessGate'

/**
 * Wraps student-only routes: redirects to /student-unavailable when access is disabled.
 * Allows /student-unavailable to render; re-enabling access redirects away from that page.
 *
 * Can be used two ways:
 *   - As a layout route (renders nested <Outlet />)
 *   - As a wrapper with explicit `children`, for role-conditional gating.
 */
function StudentAccessGate({ children }) {
  const location = useLocation()
  const { loading, enabled, onUnavailableRoute } = useStudentAccessGate()

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-dm-background">
        <p className="text-sm text-dm-muted">Loading…</p>
      </div>
    )
  }

  if (!enabled && !onUnavailableRoute) {
    return <Navigate to="/student-unavailable" replace state={{ from: location }} />
  }

  if (enabled && location.pathname === '/student-unavailable') {
    return <Navigate to="/home" replace />
  }

  return children ?? <Outlet />
}

export default StudentAccessGate
