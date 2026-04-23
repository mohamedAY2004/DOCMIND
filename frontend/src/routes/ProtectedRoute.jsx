import { Navigate, Outlet } from 'react-router-dom'
import useAuth from '../hooks/useAuth'

const HOME_BY_ROLE = {
  admin: '/admin',
  instructor: '/instructor',
  student: '/home',
}

function ProtectedRoute({ allowedRoles }) {
  const { isAuthenticated, role } = useAuth()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (allowedRoles && !allowedRoles.includes(role)) {
    return <Navigate to={HOME_BY_ROLE[role] || '/home'} replace />
  }

  return <Outlet />
}

export default ProtectedRoute
export { HOME_BY_ROLE }
