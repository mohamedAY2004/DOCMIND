import { useCallback, useLayoutEffect, useReducer, useRef } from 'react'
import { cancelMessage } from '../services/chatService'

function normalize(message, role) {
  return { ...message, role: message.role === 'user' ? 'user' : role,
    text: message.text ?? '', citations: message.citations ?? [],
    generationStatus: message.generationStatus ?? 'complete', groundingStatus: message.groundingStatus ?? null }
}

function initial(messages) {
  return { messages, status: 'idle', isTyping: false, streamingId: null,
    loadingHistory: false, loadingOlder: false, hasOlderMessages: false,
    errorMessage: '', lastFailedText: '', historyError: false }
}

function reducer(state, action) {
  if (action.type === 'reset') return initial(action.messages)
  if (action.type === 'patch') return { ...state, ...action.patch }
  if (action.type === 'messages') return { ...state, messages: action.update(state.messages) }
  return state
}

function friendlyError(error) {
  if (error?.name === 'AbortError' || error?.code === 'ERR_CANCELED') return 'The response was stopped. You can retry it.'
  if (!navigator.onLine) return 'You appear to be offline. Please check your connection and try again.'
  return error?.response?.data?.message || error?.message || 'Something went wrong. Please try again.'
}

/** Owns history and generation for one conversation. Adapters supply transport only.
 * Every async continuation belongs to a scope or request; disposal revokes ownership.
 */
export default function useChatSession({ conversationId, scopeId = '', resetKey = 0, adapter, onConversationCreated, onHistoryLoaded }) {
  const [state, dispatch] = useReducer(reducer, adapter.welcome, initial)
  const scope = useRef(null)
  const request = useRef(null)
  const history = useRef(null)
  const historyPage = useRef(0)
  const callbacks = useRef({ onConversationCreated, onHistoryLoaded })
  useLayoutEffect(() => { callbacks.current = { onConversationCreated, onHistoryLoaded } })

  const abort = useCallback(() => {
    const active = request.current
    request.current = null
    active?.controller.abort()
    if (active?.replyId) void (adapter.cancel || cancelMessage)(active.replyId).catch(() => {})
    history.current?.abort()
    history.current = null
  }, [adapter])

  const loadHistory = useCallback(async (owner, page) => {
    if (history.current) return
    const controller = new AbortController()
    history.current = controller
    const owns = () => scope.current === owner && history.current === controller
    dispatch({ type: 'patch', patch: { ...(page === 1 ? { loadingHistory: true } : { loadingOlder: true }), historyError: false, errorMessage: '' } })
    try {
      const response = await adapter.history(owner.conversationId, { page, order: 'desc', signal: controller.signal })
      if (!owns()) return
      const items = [...response.items].reverse().map((message) => normalize(message, adapter.role))
      dispatch({ type: 'messages', update: (previous) => page === 1
        ? (items.length ? items : adapter.welcome)
        : [...items.filter((item) => !previous.some((old) => old.id === item.id)), ...previous] })
      dispatch({ type: 'patch', patch: { hasOlderMessages: response.page < response.totalPages, status: 'idle' } })
      historyPage.current = response.page
      callbacks.current.onHistoryLoaded?.(items, page === 1)
    } catch (error) {
      if (owns()) dispatch({ type: 'patch', patch: { errorMessage: friendlyError(error), status: 'error', historyError: true } })
    } finally {
      if (owns()) {
        history.current = null
        dispatch({ type: 'patch', patch: { loadingHistory: false, loadingOlder: false } })
      }
    }
  }, [adapter])

  useLayoutEffect(() => {
    // A newly created conversation continues the same request after its parent selects it.
    if (scope.current?.conversationId === conversationId && scope.current?.scopeId === scopeId && scope.current?.resetKey === resetKey) return
    abort()
    const owner = { conversationId, scopeId, resetKey }
    scope.current = owner
    historyPage.current = 0
    dispatch({ type: 'reset', messages: adapter.welcome })
    callbacks.current.onHistoryLoaded?.([], true)
    if (conversationId && adapter.history) void loadHistory(owner, 1)
  }, [conversationId, scopeId, resetKey, adapter, abort, loadHistory])

  useLayoutEffect(() => () => { abort(); scope.current = null }, [abort])

  const sendMessage = useCallback(async (text) => {
    const trimmed = text.trim()
    if (!trimmed || request.current || history.current) return
    const owner = scope.current
    if (!owner) return
    const active = { controller: new AbortController(), replyId: null, text: trimmed }
    request.current = active
    const owns = () => request.current === active && scope.current === owner
    const patch = (value) => { if (owns()) dispatch({ type: 'patch', patch: value }) }
    const update = (fn) => { if (owns()) dispatch({ type: 'messages', update: fn }) }
    const tempId = `pending-${crypto.randomUUID()}`
    active.tempId = tempId
    patch({ status: 'loading', isTyping: true, errorMessage: '', lastFailedText: '' })
    update((previous) => [...previous, { id: tempId, role: 'user', text: trimmed, generationStatus: 'pending' }])
    let failed = false
    let terminal = false
    try {
      if (!owner.conversationId) {
        if (!adapter.create) throw new Error('Please upload a document before sending a message.')
        const conversation = await adapter.create(owner.scopeId, { signal: active.controller.signal })
        if (!owns()) return
        owner.conversationId = conversation.id
        callbacks.current.onConversationCreated?.(conversation)
      }
      if (!owns()) return
      await adapter.stream(owner.conversationId, trimmed, {
        signal: active.controller.signal,
        onEvent(event, payload) {
          if (!owns()) return
          if (event === 'message.created') {
            const user = normalize(payload.userMessage, adapter.role)
            const reply = normalize(payload.reply, adapter.role)
            active.replyId = reply.id
            update((previous) => [...previous.filter((message) => message.id !== tempId && message.id !== user.id && message.id !== reply.id), user, reply])
            patch({ streamingId: reply.id, isTyping: false, status: 'streaming' })
          } else if (event === 'answer.delta') {
            update((previous) => previous.map((message) => message.id === payload.replyId ? { ...message, text: message.text + payload.delta } : message))
          } else if (event === 'answer.citations') {
            update((previous) => previous.map((message) => message.id === payload.replyId ? { ...message, citations: payload.citations, groundingStatus: payload.groundingStatus } : message))
          } else if (event === 'answer.completed') {
            terminal = true
            const reply = normalize(payload.reply, adapter.role)
            update((previous) => previous.map((message) => message.id === reply.id ? reply : message))
            if (reply.generationStatus !== 'complete') {
              failed = true
              patch({ status: 'error', lastFailedText: trimmed, errorMessage: 'The response was interrupted. You can retry it.' })
            }
          } else if (event === 'answer.failed') {
            terminal = true
            failed = true
            update((previous) => previous.map((message) => message.id === payload.replyId ? { ...message, generationStatus: 'failed' } : message))
            patch({ status: 'error', lastFailedText: trimmed, errorMessage: payload.message || 'Generation failed.' })
          }
        },
      })
      if (!terminal) throw new Error('The response ended before completion. You can retry it.')
      if (!failed) patch({ status: 'idle' })
    } catch (error) {
      patch({ status: 'error', errorMessage: friendlyError(error), lastFailedText: trimmed })
      update((previous) => previous.map((message) => message.id === (active.replyId || tempId) ? { ...message, generationStatus: 'failed' } : message))
    } finally {
      if (owns()) {
        patch({ streamingId: null, isTyping: false })
        request.current = null
      }
    }
  }, [adapter])

  const stopGeneration = useCallback(() => {
    const active = request.current
    if (!active) return
    abort()
    dispatch({ type: 'messages', update: (previous) => previous.map((message) => message.id === (active.replyId || active.tempId) ? { ...message, generationStatus: 'cancelled' } : message) })
    dispatch({ type: 'patch', patch: { streamingId: null, isTyping: false, status: 'error',
      errorMessage: 'The response was stopped. You can retry it.', lastFailedText: active.text } })
  }, [abort])

  return { ...state, sendMessage, stopGeneration,
    retry: () => sendMessage(state.lastFailedText),
    dismissError: () => dispatch({ type: 'patch', patch: { errorMessage: '', status: 'idle' } }),
    loadOlder: () => state.hasOlderMessages && scope.current && loadHistory(scope.current, historyPage.current + 1),
    retryHistory: () => scope.current?.conversationId && loadHistory(scope.current, historyPage.current + 1),
  }
}
