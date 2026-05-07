import { useCallback, useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'
import {
  createTutorConversation,
  getTutorMessages,
  sendTutorMessage,
} from '../services/chatService'
import useStreamingText from './useStreamingText'

/**
 * Produce a user-friendly error message from an axios/fetch error.
 */
function friendlyError(err) {
  if (err?.code === 'ECONNABORTED' || err?.message?.includes('timeout')) {
    return 'The response took too long. The server may be under heavy load — please try again.'
  }
  if (!navigator.onLine) {
    return 'You appear to be offline. Please check your connection and try again.'
  }
  const code = err?.response?.data?.code
  if (code === 'SUBJECT_NOT_READY') {
    return err?.response?.data?.message || 'This subject has no indexed materials yet. Please check back later.'
  }
  if (code === 'FILES_NOT_READY') {
    return 'Materials are still being processed. Please wait a moment.'
  }
  const status = err?.response?.status
  if (status >= 500) {
    return 'The server encountered an error. Please try again in a moment.'
  }
  return 'The tutor could not reply. Please try again.'
}

/**
 * Tutor-chat hook — a subject-scoped conversation controller. The parent
 * owns the active `conversationId`:
 *   • `null`  → "new chat" mode. The first send lazily POSTs a fresh
 *     conversation and bubbles the new id up through `onConversationCreated`.
 *   • string  → resume mode. The hook fetches the stored message history on
 *     mount / when the id changes.
 *
 * Surfaces friendly toasts for the `SUBJECT_NOT_READY` contract defined in
 * API_SPECIFICATION.md §8.3.
 */
export default function useTutorChat({
  subjectId,
  conversationId,
  onConversationCreated,
}) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [lastFailedText, setLastFailedText] = useState('')
  const textareaRef = useRef(null)
  const creatingRef = useRef(false)
  const onCreatedRef = useRef(onConversationCreated)

  useEffect(() => {
    onCreatedRef.current = onConversationCreated
  }, [onConversationCreated])

  const { streamingId, streamReply, stopStreaming } = useStreamingText(setMessages)

  // Load history when the active conversation changes. A `null` conversation
  // id means the user wants a fresh chat, so we just clear local state.
  useEffect(() => {
    stopStreaming()
    setInput('')
    setIsTyping(false)
    setErrorMessage('')
    setLastFailedText('')

    if (!conversationId) {
      setMessages([])
      setLoadingHistory(false)
      return
    }

    let cancelled = false
    setMessages([])
    setLoadingHistory(true)
    getTutorMessages(conversationId)
      .then((items) => {
        if (cancelled) return
        setMessages(
          items.map((m) => ({
            id: m.id,
            role: m.role === 'user' ? 'user' : 'assistant',
            text: m.text ?? '',
            createdAt: m.createdAt,
          })),
        )
      })
      .catch((err) => {
        if (!cancelled) {
          if (err?.code === 'ECONNABORTED') {
            toast.error('Loading conversation timed out. Please try again.')
          } else {
            toast.error('Could not load this conversation.')
          }
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingHistory(false)
      })

    return () => {
      cancelled = true
    }
  }, [conversationId, stopStreaming])

  const appendUserMessage = useCallback((text, overrides = {}) => {
    const id = overrides.id || `user-${Date.now()}`
    setMessages((prev) => [
      ...prev,
      {
        id,
        role: 'user',
        text,
        createdAt: Date.now(),
      },
    ])
    return id
  }, [])

  const ensureConversation = useCallback(async () => {
    if (conversationId) return conversationId
    if (creatingRef.current) return null
    creatingRef.current = true
    try {
      const conv = await createTutorConversation(subjectId)
      const newId = conv?.id ?? null
      if (newId) onCreatedRef.current?.(conv)
      return newId
    } catch (err) {
      const code = err?.response?.data?.code
      if (code === 'SUBJECT_NOT_READY') {
        toast.error(
          'This subject has no indexed materials yet. Please check back later.',
        )
      } else if (code !== 'STUDENT_ACCESS_DISABLED') {
        if (err?.code === 'ECONNABORTED') {
          toast.error('Request timed out. Please try again.')
        } else {
          toast.error('Could not start the tutor conversation.')
        }
      }
      return null
    } finally {
      creatingRef.current = false
    }
  }, [conversationId, subjectId])

  const fetchReply = useCallback(
    async (text, tempId) => {
      const activeId = await ensureConversation()
      if (!activeId) {
        // Rollback optimistic user message
        setMessages((prev) => prev.filter((m) => m.id !== tempId))
        setInput(text)
        return
      }

      setIsTyping(true)
      setErrorMessage('')
      try {
        const { userMessage, reply } = await sendTutorMessage(activeId, text)
        if (userMessage?.id) {
          setMessages((prev) => {
            const last = prev[prev.length - 1]
            if (!last || last.role !== 'user') return prev
            return prev.map((m, i) =>
              i === prev.length - 1 ? { ...m, id: userMessage.id } : m,
            )
          })
        }
        const msgId = reply?.id || `ai-${Date.now()}`
        const replyText = reply?.text || ''
        setMessages((prev) => [
          ...prev,
          { id: msgId, role: 'assistant', text: '', createdAt: Date.now() },
        ])
        setIsTyping(false)
        streamReply(replyText, msgId)
      } catch (err) {
        setIsTyping(false)
        const msg = friendlyError(err)
        setErrorMessage(msg)
        setLastFailedText(text)
        // Rollback the optimistic user message
        setMessages((prev) => prev.filter((m) => m.id !== tempId))
      }
    },
    [ensureConversation, streamReply],
  )

  const sendMessage = useCallback(
    (e) => {
      e?.preventDefault()
      const text = input.trim()
      if (!text || isTyping || streamingId) return
      setErrorMessage('')
      setLastFailedText('')
      const tempId = appendUserMessage(text)
      setInput('')
      if (textareaRef.current) textareaRef.current.style.height = 'auto'
      fetchReply(text, tempId)
    },
    [input, isTyping, streamingId, appendUserMessage, fetchReply],
  )

  const retry = useCallback(() => {
    if (!lastFailedText) return
    setErrorMessage('')
    const text = lastFailedText
    setLastFailedText('')
    const tempId = appendUserMessage(text)
    fetchReply(text, tempId)
  }, [lastFailedText, appendUserMessage, fetchReply])

  const resetChat = useCallback(() => {
    stopStreaming()
    setMessages([])
    setInput('')
    setIsTyping(false)
    setErrorMessage('')
    setLastFailedText('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }, [stopStreaming])

  const handleInputChange = useCallback((e) => {
    setInput(e.target.value)
    const el = e.target
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }, [])

  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        sendMessage()
      }
    },
    [sendMessage],
  )

  const dismissError = useCallback(() => {
    setErrorMessage('')
  }, [])

  return {
    messages,
    input,
    isTyping,
    streamingId,
    textareaRef,
    loadingHistory,
    errorMessage,
    lastFailedText,
    sendMessage,
    retry,
    resetChat,
    dismissError,
    handleInputChange,
    handleKeyDown,
  }
}
