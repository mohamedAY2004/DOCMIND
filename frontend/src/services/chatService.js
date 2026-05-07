import apiClient, { UPLOAD_TIMEOUT, LLM_TIMEOUT } from './apiClient'

/**
 * Chat service — talks to the conversation endpoints described in
 * API_SPECIFICATION.md §8.
 *
 * Doc chat (students upload ad-hoc files and talk to them):
 *   GET    /chat/doc/conversations                    list { items, page, … }
 *   POST   /chat/doc/conversations                    multipart files[]
 *   DELETE /chat/doc/conversations/:id                remove conversation
 *   GET    /chat/doc/conversations/:id/messages       paginated history
 *   POST   /chat/doc/conversations/:id/files          multipart file
 *   DELETE /chat/doc/conversations/:id/files/:fileId
 *   GET    /chat/doc/conversations/:id/files
 *   POST   /chat/doc/conversations/:id/messages       { message } → { userMessage, reply }
 *
 * Tutor chat (subject-scoped):
 *   GET    /chat/tutor/conversations?subjectId=…      list { items, page, … }
 *   POST   /chat/tutor/conversations                  { subjectId } → Conversation
 *   DELETE /chat/tutor/conversations/:id
 *   GET    /chat/tutor/conversations/:id/messages     paginated history
 *   POST   /chat/tutor/conversations/:id/messages     { message } → { userMessage, reply }
 *
 * Feedback:
 *   POST   /chat/messages/:messageId/feedback         { feedback: 'up' | 'down' }
 *   DELETE /chat/messages/:messageId/feedback
 */

const DEFAULT_HISTORY_PAGE_SIZE = 50
const DEFAULT_CONV_PAGE_SIZE = 20

function unwrapList(data) {
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.items)) return data.items
  return []
}

/* ------------------------------------------------------------------ */
/* Document chat                                                      */
/* ------------------------------------------------------------------ */

export async function listDocConversations(opts) {
  const { page = 1, pageSize = DEFAULT_CONV_PAGE_SIZE } = opts || {}
  const { data } = await apiClient.get('/chat/doc/conversations', {
    params: { page, pageSize },
  })
  return unwrapList(data)
}

export async function getDocMessages(
  conversationId,
  { page = 1, pageSize = DEFAULT_HISTORY_PAGE_SIZE } = {},
) {
  const { data } = await apiClient.get(
    `/chat/doc/conversations/${conversationId}/messages`,
    { params: { page, pageSize } },
  )
  return unwrapList(data)
}

export async function deleteDocConversation(conversationId) {
  await apiClient.delete(`/chat/doc/conversations/${conversationId}`)
  return { id: conversationId }
}

export async function updateDocConversation(conversationId, title) {
  const { data } = await apiClient.patch(
    `/chat/doc/conversations/${conversationId}`,
    { title },
  )
  return data
}

export async function createDocConversation(files, { onUploadProgress } = {}) {
  const formData = new FormData()
  const list = Array.isArray(files) ? files : [files]
  list.forEach((f) => formData.append('files', f))

  const { data } = await apiClient.post('/chat/doc/conversations', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    ...UPLOAD_TIMEOUT,
    ...(onUploadProgress ? { onUploadProgress } : {}),
  })
  // The API returns { conversation: { id, title, … }, files: [...] }.
  // Flatten so callers can use conv.id, conv.title, conv.files, etc.
  if (data?.conversation) {
    return { ...data.conversation, files: data.files ?? [] }
  }
  return data
}

export async function addDocFile(conversationId, file, { onUploadProgress } = {}) {
  const formData = new FormData()
  formData.append('file', file)

  const { data } = await apiClient.post(
    `/chat/doc/conversations/${conversationId}/files`,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      ...UPLOAD_TIMEOUT,
      ...(onUploadProgress ? { onUploadProgress } : {}),
    },
  )
  return data
}

export async function removeDocFile(conversationId, fileId) {
  await apiClient.delete(
    `/chat/doc/conversations/${conversationId}/files/${fileId}`,
  )
  return { id: fileId }
}

export async function listDocFiles(conversationId) {
  const { data } = await apiClient.get(
    `/chat/doc/conversations/${conversationId}/files`,
  )
  return data
}

export async function sendDocMessage(conversationId, message) {
  const { data } = await apiClient.post(
    `/chat/doc/conversations/${conversationId}/messages`,
    { message },
    LLM_TIMEOUT,
  )
  return data
}

/* ------------------------------------------------------------------ */
/* Tutor chat                                                         */
/* ------------------------------------------------------------------ */

export async function listTutorConversations(
  subjectId,
  { page = 1, pageSize = DEFAULT_CONV_PAGE_SIZE } = {},
) {
  const { data } = await apiClient.get('/chat/tutor/conversations', {
    params: { subjectId, page, pageSize },
  })
  return unwrapList(data)
}

export async function getTutorMessages(
  conversationId,
  { page = 1, pageSize = DEFAULT_HISTORY_PAGE_SIZE } = {},
) {
  const { data } = await apiClient.get(
    `/chat/tutor/conversations/${conversationId}/messages`,
    { params: { page, pageSize } },
  )
  return unwrapList(data)
}

export async function createTutorConversation(subjectId) {
  const { data } = await apiClient.post('/chat/tutor/conversations', {
    subjectId,
  })
  return data
}

export async function deleteTutorConversation(conversationId) {
  await apiClient.delete(`/chat/tutor/conversations/${conversationId}`)
  return { id: conversationId }
}

export async function updateTutorConversation(conversationId, title) {
  const { data } = await apiClient.patch(
    `/chat/tutor/conversations/${conversationId}`,
    { title },
  )
  return data
}

export async function sendTutorMessage(conversationId, message) {
  const { data } = await apiClient.post(
    `/chat/tutor/conversations/${conversationId}/messages`,
    { message },
    LLM_TIMEOUT,
  )
  return data
}

/* ------------------------------------------------------------------ */
/* Feedback                                                           */
/* ------------------------------------------------------------------ */

export async function sendMessageFeedback(messageId, feedback) {
  const { data } = await apiClient.post(
    `/chat/messages/${messageId}/feedback`,
    { feedback },
  )
  return data
}

export async function clearMessageFeedback(messageId) {
  await apiClient.delete(`/chat/messages/${messageId}/feedback`)
  return { id: messageId }
}
