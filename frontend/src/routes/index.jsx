import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import useAuth from '../hooks/useAuth'
import ProtectedRoute, { HOME_BY_ROLE } from './ProtectedRoute'
import StudentAccessGate from '../components/layout/StudentAccessGate'

const Login = lazy(() => import('../pages/Login'))
const InstructorHome = lazy(() => import('../pages/InstructorHome'))
const UserHome = lazy(() => import('../pages/UserHome'))
const ChatWithDoc = lazy(() => import('../pages/ChatWithDoc'))
const ChatWithTutors = lazy(() => import('../pages/ChatWithTutors'))
const TutorChat = lazy(() => import('../pages/TutorChat'))
const InstructorSubject = lazy(() => import('../pages/InstructorSubject'))
const AdminDashboard = lazy(() => import('../pages/admin/AdminDashboard'))
const ManageUsers = lazy(() => import('../pages/admin/ManageUsers'))
const ManageInstructors = lazy(() => import('../pages/admin/ManageInstructors'))
const ManageSubjects = lazy(() => import('../pages/admin/ManageSubjects'))
const ManageSemesters = lazy(() => import('../pages/admin/ManageSemesters'))
const SubjectFeedback = lazy(() => import('../pages/admin/SubjectFeedback'))
const Analytics = lazy(() => import('../pages/admin/Analytics'))
const SystemAccess = lazy(() => import('../pages/admin/SystemAccess'))
const QualityReport = lazy(() => import('../pages/admin/QualityReport'))
const StudentUnavailable = lazy(() => import('../pages/StudentUnavailable'))

function RootRedirect() {
  const { isAuthenticated, role, ready } = useAuth()
  if (!ready) return null
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <Navigate to={HOME_BY_ROLE[role] || '/home'} replace />
}

function LoginGate() {
  const { isAuthenticated, role, ready } = useAuth()
  if (!ready) return null
  if (isAuthenticated) {
    return <Navigate to={HOME_BY_ROLE[role] || '/home'} replace />
  }
  return <Login />
}

export function AppRoutes() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center bg-dm-background text-dm-muted">Loading…</div>}>
    <Routes>
      <Route path="/" element={<RootRedirect />} />
      <Route path="/login" element={<LoginGate />} />

      {/* Student routes */}
      <Route element={<ProtectedRoute allowedRoles={['student']} />}>
        <Route element={<StudentAccessGate />}>
          <Route path="/home" element={<UserHome />} />
          <Route path="/chat" element={<ChatWithDoc />} />
          <Route path="/tutors" element={<ChatWithTutors />} />
          <Route path="/tutors/chat" element={<TutorChat />} />
          <Route path="/student-unavailable" element={<StudentUnavailable />} />
        </Route>
      </Route>

      {/* Instructor routes */}
      <Route element={<ProtectedRoute allowedRoles={['instructor']} />}>
        <Route path="/instructor" element={<InstructorHome />} />
        <Route path="/instructor/subject/:subjectId" element={<InstructorSubject />} />
      </Route>

      {/* Admin routes */}
      <Route element={<ProtectedRoute allowedRoles={['admin']} />}>
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/admin/users" element={<ManageUsers />} />
        <Route path="/admin/instructors" element={<ManageInstructors />} />
        <Route path="/admin/subjects" element={<ManageSubjects />} />
        <Route path="/admin/semesters" element={<ManageSemesters />} />
        <Route path="/admin/feedback" element={<SubjectFeedback />} />
        <Route path="/admin/analytics" element={<Analytics />} />
        <Route path="/admin/system-access" element={<SystemAccess />} />
        <Route path="/admin/quality" element={<QualityReport />} />
      </Route>
    </Routes>
    </Suspense>
  )
}
