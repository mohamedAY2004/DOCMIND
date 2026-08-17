import apiClient, {
  API_BASE_URL,
  UPLOAD_TIMEOUT,
  LLM_TIMEOUT,
  readCookie,
  refreshBrowserSession,
} from './apiClient'

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

export async function streamDocMessage(conversationId, message, options = {}) {
  try {
    return await streamMessage(
      `/chat/doc/conversations/${conversationId}/messages/stream`,
      message,
      options,
    )
  } catch (error) {
    if (!streamingDisabled(error)) throw error
    const response = await sendDocMessage(conversationId, message)
    dispatchBufferedReply(response, options.onEvent)
  }
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

export async function streamTutorMessage(conversationId, message, options = {}) {
  try {
    return await streamMessage(
      `/chat/tutor/conversations/${conversationId}/messages/stream`,
      message,
      options,
    )
  } catch (error) {
    if (!streamingDisabled(error)) throw error
    const response = await sendTutorMessage(conversationId, message)
    dispatchBufferedReply(response, options.onEvent)
  }
}

export async function cancelMessage(messageId) {
  const { data } = await apiClient.post(`/chat/messages/${messageId}/cancel`)
  return data
}

export async function getCitationView(messageId, citationId) {
  const { data } = await apiClient.get(
    `/chat/messages/${messageId}/citations/${citationId}/view`,
  )
  return data
}

export async function streamMessage(
  path,
  message,
  { signal, onEvent, sessionRetry = false } = {},
) {
  const controller = new AbortController()
  let timedOut = false
  let watchdog = null
  const armWatchdog = (delay) => {
    clearTimeout(watchdog)
    watchdog = setTimeout(() => {
      timedOut = true
      controller.abort()
    }, delay)
  }
  const abortFromCaller = () => controller.abort()
  if (signal?.aborted) controller.abort()
  else signal?.addEventListener('abort', abortFromCaller, { once: true })
  armWatchdog(60_000)

  try {
    const csrf = readCookie('docmind_csrf')
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'POST',
      credentials: 'include',
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
        ...(csrf ? { 'X-CSRF-Token': csrf } : {}),
      },
      body: JSON.stringify({ message }),
    })
    if (response.status === 401 && !sessionRetry) {
      await refreshBrowserSession()
      return streamMessage(path, message, {
        signal,
        onEvent,
        sessionRetry: true,
      })
    }
    if (!response.ok) {
      let body = null
      try {
        body = await response.json()
      } catch {
        body = null
      }
      const error = new Error(body?.message || `Request failed (${response.status})`)
      error.response = { status: response.status, data: body }
      throw error
    }
    if (!response.body) throw new Error('Streaming is not supported by this browser.')

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      armWatchdog(90_000)
      buffer += decoder.decode(value || new Uint8Array(), { stream: !done })
      const frames = buffer.split(/\r?\n\r?\n/)
      buffer = frames.pop() || ''
      for (const frame of frames) dispatchSseFrame(frame, onEvent)
      if (done) break
    }
    if (buffer.trim()) dispatchSseFrame(buffer, onEvent)
  } catch (error) {
    if (timedOut) throw new Error('The response timed out. Please retry it.')
    throw error
  } finally {
    clearTimeout(watchdog)
    signal?.removeEventListener('abort', abortFromCaller)
  }
}

function streamingDisabled(error) {
  return error?.response?.status === 404
    && /streaming chat is disabled/i.test(error?.response?.data?.message || '')
}

function dispatchBufferedReply(response, onEvent) {
  onEvent?.('message.created', response)
  onEvent?.('answer.completed', { reply: response.reply })
}

export function resolveApiUrl(url) {
  if (!url || /^[a-z][a-z\d+.-]*:/i.test(url) || !API_BASE_URL.startsWith('http')) return url
  return new URL(url, new URL(API_BASE_URL).origin).toString()
}

function dispatchSseFrame(frame, onEvent) {
  const parsed = parseSseFrame(frame)
  if (parsed) onEvent?.(parsed.event, parsed.data)
}

export function parseSseFrame(frame) {
  let event = 'message'
  const data = []
  for (const line of frame.split(/\r?\n/)) {
    if (line.startsWith('event:')) event = line.slice(6).trim()
    if (line.startsWith('data:')) data.push(line.slice(5).trimStart())
  }
  if (!data.length) return null
  const raw = data.join('\n')
  return { event, data: JSON.parse(raw) }
}

/* ------------------------------------------------------------------ */
/* Feedback                                                           */
/* ------------------------------------------------------------------ */

export async function sendMessageFeedback(messageId, feedback, details = {}) {
  const { data } = await apiClient.post(
    `/chat/messages/${messageId}/feedback`,
    { feedback, ...details },
  )
  return data
}

export async function clearMessageFeedback(messageId) {
  await apiClient.delete(`/chat/messages/${messageId}/feedback`)
  return { id: messageId }
}
