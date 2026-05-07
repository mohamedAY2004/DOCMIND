import apiClient, { UPLOAD_TIMEOUT } from './apiClient'

/**
 * Upload service — real multipart uploads.
 *
 * Materials are attached to a subject and shared with every instructor on its
 * roster (see API_SPECIFICATION.md §7). Document-chat file handling lives in
 * `chatService.js` because it creates/mutates a conversation.
 */

export async function uploadMaterial(subjectId, file, { name, onUploadProgress } = {}) {
  const formData = new FormData()
  formData.append('file', file)
  if (name) formData.append('name', name)

  const { data } = await apiClient.post(
    `/subjects/${subjectId}/materials`,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      ...UPLOAD_TIMEOUT,
      ...(onUploadProgress ? { onUploadProgress } : {}),
    },
  )
  return data
}
