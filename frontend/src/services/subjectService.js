import { parseList } from './pageResponse'
import apiClient from './apiClient'
import { streamMessage } from './chatService'

/**
 * Subject service — talks to the real backend.
 *
 * Backend contract (see API_SPECIFICATION.md §6 / §7):
 *   GET    /subjects/student
 *   GET    /subjects/instructor?instructorId=...
 *   GET    /subjects/:subjectId
 *   GET    /subjects/:subjectId/instructors
 *   GET    /subjects/:subjectId/materials
 *   POST   /subjects/:subjectId/materials    (multipart — see uploadService)
 *   PATCH  /subjects/:subjectId/materials/:materialId
 *   DELETE /subjects/:subjectId/materials/:materialId
 */

export async function getStudentSubjects() {
  const { data } = await apiClient.get('/subjects/student')
  return parseList(data)
}

export async function getInstructorSubjects(instructorId) {
  const { data } = await apiClient.get('/subjects/instructor', {
    params: instructorId ? { instructorId } : undefined,
  })
  return parseList(data)
}

/**
 * Semesters list — used by the student/instructor subject pages to label and
 * order the per-semester sections. Endpoint is open to any authenticated user
 * (not admin-only), so it is exposed here rather than via the admin service.
 * GET /semesters → [{ id, label, sortOrder, state, isCurrent, ... }] (newest first)
 */
export async function getSemesters() {
  const { data } = await apiClient.get('/semesters')
  return parseList(data)
}

export async function getSubjectById(subjectId) {
  const { data } = await apiClient.get(`/subjects/${subjectId}`)
  return data
}

export async function getSubjectInstructors(subjectId) {
  const { data } = await apiClient.get(`/subjects/${subjectId}/instructors`)
  return parseList(data)
}

export async function getSubjectMaterials(subjectId, options = {}) {
  const { data } = await apiClient.get(`/subjects/${subjectId}/materials`, options)
  return parseList(data)
}

export async function deleteSubjectMaterial(subjectId, materialId, options = {}) {
  await apiClient.delete(`/subjects/${subjectId}/materials/${materialId}`, options)
  return { id: materialId }
}

/**
 * Download a previously uploaded material file. Allowed for any instructor on
 * the roster (super or viewer) and admins, including on archived semesters —
 * on archived terms it is the only material action that stays available.
 * GET /subjects/:subjectId/materials/:materialId/download → file blob
 */
export async function downloadSubjectMaterial(subjectId, materialId, filename, { signal } = {}) {
  const { data } = await apiClient.get(
    `/subjects/${subjectId}/materials/${materialId}/download`,
    { responseType: 'blob', signal },
  )
  signal?.throwIfAborted()
  const url = window.URL.createObjectURL(data)
  const link = document.createElement('a')
  link.href = url
  link.download = filename || 'material'
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

/**
 * Instructor test-bot — stateless preview of what students will see.
 * POST /subjects/:subjectId/test-bot  { message } → { reply }
 */
export function streamTestBotMessage(subjectId, message, options = {}) {
  return streamMessage(`/subjects/${subjectId}/test-bot/stream`, message, options)
}
