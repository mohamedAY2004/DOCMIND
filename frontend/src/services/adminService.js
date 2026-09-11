import { parseList, parsePage } from './pageResponse'
import apiClient from './apiClient'

/**
 * Admin service — see API_SPECIFICATION.md §10.
 *
 * All endpoints require role=admin. 403 FORBIDDEN is returned by the server
 * for any other caller; the apiClient interceptors will redirect away on
 * STUDENT_ACCESS_DISABLED / 401, so callers only need to handle data + the
 * generic error toast pattern.
 */

// ---------------- Users ----------------

export async function getUsers({ signal, ...params } = {}) {
  const { data } = await apiClient.get('/admin/users', { params, signal })
  return parsePage(data)
}

export async function createUser(body) {
  const { data } = await apiClient.post('/admin/users', body)
  return data
}

export async function updateUser(userId, patch) {
  const { data } = await apiClient.patch(`/admin/users/${userId}`, patch)
  return data
}

export async function setUserStatus(userId, status) {
  const { data } = await apiClient.patch(`/admin/users/${userId}/status`, { status })
  return data
}

export async function resetUserPassword(userId) {
  const { data } = await apiClient.post(`/admin/users/${userId}/reset-password`)
  return data
}

export async function deleteUser(userId) {
  await apiClient.delete(`/admin/users/${userId}`)
}

export async function getUserSubjects(userId) {
  const { data } = await apiClient.get(`/admin/users/${userId}/subjects`)
  return parseList(data)
}

// ---------------- Subjects (CRUD) ----------------

export async function listSubjects({ signal, ...params } = {}) {
  const { data } = await apiClient.get('/admin/subjects', { params, signal })
  return parsePage(data)
}

export async function createSubject(body) {
  const { data } = await apiClient.post('/admin/subjects', body)
  return data
}

export async function updateSubject(subjectId, patch) {
  const { data } = await apiClient.patch(`/admin/subjects/${subjectId}`, patch)
  return data
}

export async function deleteSubject(subjectId) {
  await apiClient.delete(`/admin/subjects/${subjectId}`)
}

// ---------------- Stats / feedback / analytics ----------------

export async function getSubjectStats({ signal, ...params } = {}) {
  const { data } = await apiClient.get('/admin/subjects/stats', { params, signal })
  return parsePage(data)
}

export async function getFeedback({ signal, ...params } = {}) {
  const { data } = await apiClient.get('/admin/feedback', { params, signal })
  return parsePage(data)
}

export async function getActivityLog(limit = 20) {
  const { data } = await apiClient.get('/admin/activity', {
    params: { limit },
  })
  return parseList(data)
}

export async function getDailyUsage({
  days = 14,
  semesterId,
  subjectId,
  instructorId,
} = {}) {
  // Backend accepts `days` (int, 1..90) plus optional semesterId / subjectId /
  // instructorId scoping; keep the client aligned with the contract declared in
  // backend/src/routes/admin_router.py.
  const params = { days }
  if (semesterId) params.semesterId = semesterId
  if (subjectId) params.subjectId = subjectId
  if (instructorId) params.instructorId = instructorId
  const { data } = await apiClient.get('/admin/analytics/daily', { params })
  return data
}

export async function getSemesters() {
  const { data } = await apiClient.get('/semesters')
  return parseList(data)
}

export async function createSemester(body) {
  const { data } = await apiClient.post('/admin/semesters', body)
  return data
}

export async function updateSemester(semesterId, patch) {
  const { data } = await apiClient.patch(`/admin/semesters/${semesterId}`, patch)
  return data
}

export async function deleteSemester(semesterId) {
  await apiClient.delete(`/admin/semesters/${semesterId}`)
}
