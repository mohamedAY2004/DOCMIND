import apiClient from './apiClient'

/**
 * Student access policy (exam / maintenance).
 *
 * Backend contract (see API_SPECIFICATION.md §5):
 *   GET    /system/student-access           → { enabled, message, updatedAt }
 *   PATCH  /admin/system/student-access     body: { enabled, message? }
 */

export async function getStudentAccess() {
  const { data } = await apiClient.get('/system/student-access')
  return data
}

/**
 * @param {{ enabled: boolean, message?: string }} payload
 */
export async function setStudentAccess(payload) {
  const { data } = await apiClient.patch('/admin/system/student-access', payload)
  return data
}
