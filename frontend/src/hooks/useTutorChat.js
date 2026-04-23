import { useCallback, useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'
import {
  createTutorConversation,
  getTutorMessages,
  sendTutorMessage,
} from '../services/chatService'
import useStreamingText from './useStreamingText'

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
      .catch(() => {
        if (!cancelled) toast.error('Could not load this conversation.')
      })
      .finally(() => {
        if (!cancelled) setLoadingHistory(false)
      })

    return () => {
      cancelled = true
    }
  }, [conversationId, stopStreaming])

  const appendUserMessage = useCallback((text, overrides = {}) => {
    setMessages((prev) => [
      ...prev,
      {
        id: overrides.id || `user-${Date.now()}`,
        role: 'user',
        text,
        createdAt: Date.now(),
      },
    ])
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
        toast.error('Could not start the tutor conversation.')
      }
      return null
    } finally {
      creatingRef.current = false
    }
  }, [conversationId, subjectId])

  const fetchReply = useCallback(
    async (text) => {
      const activeId = await ensureConversation()
      if (!activeId) return

      setIsTyping(true)
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
        const code = err?.response?.data?.code
        if (code === 'SUBJECT_NOT_READY') {
          toast.error(
            'This subject has no indexed materials yet. Please check back later.',
          )
        } else {
          toast.error('The tutor could not reply. Please try again.')
        }
      }
    },
    [ensureConversation, streamReply],
  )

  const sendMessage = useCallback(
    (e) => {
      e?.preventDefault()
      const text = input.trim()
      if (!text || isTyping || streamingId) return
      appendUserMessage(text)
      setInput('')
      if (textareaRef.current) textareaRef.current.style.height = 'auto'
      fetchReply(text)
    },
    [input, isTyping, streamingId, appendUserMessage, fetchReply],
  )

  const sendSuggestion = useCallback(
    (text) => {
      if (isTyping || streamingId) return
      appendUserMessage(text)
      fetchReply(text)
    },
    [isTyping, streamingId, appendUserMessage, fetchReply],
  )

  const resetChat = useCallback(() => {
    stopStreaming()
    setMessages([])
    setInput('')
    setIsTyping(false)
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

  return {
    messages,
    input,
    isTyping,
    streamingId,
    textareaRef,
    loadingHistory,
    sendMessage,
    sendSuggestion,
    resetChat,
    handleInputChange,
    handleKeyDown,
  }
}
