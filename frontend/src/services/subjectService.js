import apiClient from './apiClient'

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
  return data
}

export async function getInstructorSubjects(instructorId) {
  const { data } = await apiClient.get('/subjects/instructor', {
    params: instructorId ? { instructorId } : undefined,
  })
  return data
}

export async function getSubjectById(subjectId) {
  const { data } = await apiClient.get(`/subjects/${subjectId}`)
  return data
}

export async function getSubjectInstructors(subjectId) {
  const { data } = await apiClient.get(`/subjects/${subjectId}/instructors`)
  return data
}

export async function getSubjectMaterials(subjectId) {
  const { data } = await apiClient.get(`/subjects/${subjectId}/materials`)
  return data
}

export async function updateSubjectMaterial(subjectId, materialId, patch) {
  const { data } = await apiClient.patch(
    `/subjects/${subjectId}/materials/${materialId}`,
    patch,
  )
  return data
}

export async function deleteSubjectMaterial(subjectId, materialId) {
  await apiClient.delete(`/subjects/${subjectId}/materials/${materialId}`)
  return { id: materialId }
}
