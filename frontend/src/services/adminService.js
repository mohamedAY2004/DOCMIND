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

export async function getUsers(params = {}) {
  const { data } = await apiClient.get('/admin/users', { params })
  return data
}

export async function getUser(userId) {
  const { data } = await apiClient.get(`/admin/users/${userId}`)
  return data
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
  return data
}

export async function setUserSubjects(userId, subjectIds) {
  const { data } = await apiClient.put(`/admin/users/${userId}/subjects`, {
    subjectIds,
  })
  return data
}

// ---------------- Subjects (CRUD) ----------------

export async function listSubjects(params = {}) {
  const { data } = await apiClient.get('/admin/subjects', { params })
  return data
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

export async function getSubjectInstructors(subjectId) {
  const { data } = await apiClient.get(`/subjects/${subjectId}/instructors`)
  return data
}

export async function getSubjectStudents(subjectId) {
  const { data } = await apiClient.get(`/subjects/${subjectId}/students`)
  return data
}

// ---------------- Stats / feedback / analytics ----------------

export async function getSubjectStats(params = {}) {
  const { data } = await apiClient.get('/admin/subjects/stats', { params })
  return data
}

export async function getFeedback(params = {}) {
  const { data } = await apiClient.get('/admin/feedback', { params })
  return data
}

export async function getActivityLog(limit = 20) {
  const { data } = await apiClient.get('/admin/activity', {
    params: { limit },
  })
  return data
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
  return data
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
