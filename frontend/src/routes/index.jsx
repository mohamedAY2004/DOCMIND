import { Routes, Route, Navigate } from 'react-router-dom'
import useAuth from '../hooks/useAuth'
import ProtectedRoute, { HOME_BY_ROLE } from './ProtectedRoute'
import Login from '../pages/Login'
import InstructorHome from '../pages/InstructorHome'
import UserHome from '../pages/UserHome'
import ChatWithDoc from '../pages/ChatWithDoc'
import ChatWithTutors from '../pages/ChatWithTutors'
import TutorChat from '../pages/TutorChat'
import InstructorSubject from '../pages/InstructorSubject'
import AdminDashboard from '../pages/admin/AdminDashboard'
import ManageUsers from '../pages/admin/ManageUsers'
import ManageInstructors from '../pages/admin/ManageInstructors'
import ManageSubjects from '../pages/admin/ManageSubjects'
import ManageSemesters from '../pages/admin/ManageSemesters'
import SubjectFeedback from '../pages/admin/SubjectFeedback'
import Analytics from '../pages/admin/Analytics'
import SystemAccess from '../pages/admin/SystemAccess'
import StudentAccessGate from '../components/layout/StudentAccessGate'
import StudentUnavailable from '../pages/StudentUnavailable'

function RootRedirect() {
  const { isAuthenticated, role } = useAuth()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <Navigate to={HOME_BY_ROLE[role] || '/home'} replace />
}

function LoginGate() {
  const { isAuthenticated, role } = useAuth()
  if (isAuthenticated) {
    return <Navigate to={HOME_BY_ROLE[role] || '/home'} replace />
  }
  return <Login />
}

export function AppRoutes() {
  return (
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
      </Route>
    </Routes>
  )
}
