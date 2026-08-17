import { useCallback, useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'
import {
  cancelMessage,
  createTutorConversation,
  getTutorMessages,
  streamTutorMessage,
} from '../services/chatService'

function friendlyError(err) {
  if (err?.name === 'AbortError') return 'The response was stopped. You can retry it.'
  if (!navigator.onLine) return 'You appear to be offline. Please check your connection and try again.'
  const code = err?.response?.data?.code
  if (code === 'FORBIDDEN' && err?.response?.data?.details?.semesterState) return err.response.data.message
  if (code === 'SUBJECT_NOT_READY') return err?.response?.data?.message || 'This subject has no indexed materials yet.'
  if (err?.response?.status >= 500) return 'The server encountered an error. Please try again in a moment.'
  return err?.message || 'The tutor could not reply. Please try again.'
}

function normalizeMessage(message) {
  return {
    ...message,
    role: message.role === 'user' ? 'user' : 'assistant',
    text: message.text ?? '',
    citations: message.citations ?? [],
    generationStatus: message.generationStatus ?? 'complete',
    groundingStatus: message.groundingStatus ?? null,
  }
}

export default function useTutorChat({
  subjectId,
  conversationId,
  onConversationCreated,
  onFeedbackMapLoaded,
}) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [streamingId, setStreamingId] = useState(null)
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [lastFailedText, setLastFailedText] = useState('')
  const textareaRef = useRef(null)
  const creatingRef = useRef(false)
  const justCreatedIdRef = useRef(null)
  const onCreatedRef = useRef(onConversationCreated)
  const onFeedbackMapLoadedRef = useRef(onFeedbackMapLoaded)
  const controllerRef = useRef(null)
  const replyIdRef = useRef(null)

  useEffect(() => { onCreatedRef.current = onConversationCreated }, [onConversationCreated])
  useEffect(() => { onFeedbackMapLoadedRef.current = onFeedbackMapLoaded }, [onFeedbackMapLoaded])

  useEffect(() => {
    if (conversationId && conversationId === justCreatedIdRef.current) {
      justCreatedIdRef.current = null
      return
    }
    controllerRef.current?.abort()
    controllerRef.current = null
    replyIdRef.current = null
    setInput('')
    setIsTyping(false)
    setStreamingId(null)
    setErrorMessage('')
    setLastFailedText('')
    onFeedbackMapLoadedRef.current?.({})
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
        const feedback = {}
        const normalized = items.map((message) => {
          if (message.role !== 'user' && message.feedback) feedback[message.id] = message.feedback
          return normalizeMessage(message)
        })
        setMessages(normalized)
        onFeedbackMapLoadedRef.current?.(feedback)
      })
      .catch(() => { if (!cancelled) toast.error('Could not load this conversation.') })
      .finally(() => { if (!cancelled) setLoadingHistory(false) })
    return () => { cancelled = true }
  }, [conversationId])

  const appendUserMessage = useCallback((text) => {
    const id = `user-${Date.now()}`
    setMessages((prev) => [...prev, { id, role: 'user', text, createdAt: Date.now() }])
    return id
  }, [])

  const ensureConversation = useCallback(async () => {
    if (conversationId) return conversationId
    if (creatingRef.current) return null
    creatingRef.current = true
    try {
      const conversation = await createTutorConversation(subjectId)
      if (conversation?.id) {
        justCreatedIdRef.current = conversation.id
        onCreatedRef.current?.(conversation)
      }
      return conversation?.id ?? null
    } catch (err) {
      toast.error(friendlyError(err))
      return null
    } finally {
      creatingRef.current = false
    }
  }, [conversationId, subjectId])

  const fetchReply = useCallback(async (text, tempId) => {
    replyIdRef.current = null
    const activeId = await ensureConversation()
    if (!activeId) {
      setMessages((prev) => prev.filter((m) => m.id !== tempId))
      setInput(text)
      return
    }
    setIsTyping(true)
    setErrorMessage('')
    const controller = new AbortController()
    controllerRef.current = controller
    try {
      await streamTutorMessage(activeId, text, {
        signal: controller.signal,
        onEvent(event, payload) {
          if (event === 'message.created') {
            const user = normalizeMessage(payload.userMessage)
            const reply = normalizeMessage(payload.reply)
            replyIdRef.current = reply.id
            setMessages((prev) => {
              const next = prev.map((m) => (m.id === tempId ? user : m))
              return next.some((m) => m.id === reply.id) ? next : [...next, reply]
            })
            setStreamingId(reply.id)
            setIsTyping(false)
          } else if (event === 'answer.delta') {
            setMessages((prev) => prev.map((m) => (
              m.id === payload.replyId ? { ...m, text: m.text + payload.delta } : m
            )))
          } else if (event === 'answer.citations') {
            setMessages((prev) => prev.map((m) => (
              m.id === payload.replyId
                ? { ...m, citations: payload.citations, groundingStatus: payload.groundingStatus }
                : m
            )))
          } else if (event === 'answer.completed') {
            const reply = normalizeMessage(payload.reply)
            setMessages((prev) => prev.map((m) => (m.id === reply.id ? reply : m)))
            if (reply.generationStatus === 'cancelled') setLastFailedText(text)
          } else if (event === 'answer.failed') {
            setMessages((prev) => prev.map((m) => (
              m.id === payload.replyId ? { ...m, generationStatus: 'failed' } : m
            )))
            setErrorMessage(payload.message || 'Generation failed.')
            setLastFailedText(text)
          }
        },
      })
    } catch (err) {
      setErrorMessage(friendlyError(err))
      setLastFailedText(text)
      if (!replyIdRef.current) setMessages((prev) => prev.filter((m) => m.id !== tempId))
    } finally {
      if (controllerRef.current === controller) controllerRef.current = null
      setStreamingId(null)
      setIsTyping(false)
    }
  }, [ensureConversation])

  const sendMessage = useCallback((event) => {
    event?.preventDefault()
    const text = input.trim()
    if (!text || isTyping || streamingId) return
    setErrorMessage('')
    setLastFailedText('')
    const tempId = appendUserMessage(text)
    setInput('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
    void fetchReply(text, tempId)
  }, [input, isTyping, streamingId, appendUserMessage, fetchReply])

  const stopGeneration = useCallback(() => {
    controllerRef.current?.abort()
    controllerRef.current = null
    const replyId = replyIdRef.current
    if (replyId) void cancelMessage(replyId).catch(() => {})
    setMessages((prev) => prev.map((m) => (
      m.id === replyId ? { ...m, generationStatus: 'cancelled' } : m
    )))
    setStreamingId(null)
    setIsTyping(false)
  }, [])

  const retry = useCallback(() => {
    if (!lastFailedText) return
    const text = lastFailedText
    setLastFailedText('')
    setErrorMessage('')
    const tempId = appendUserMessage(text)
    void fetchReply(text, tempId)
  }, [lastFailedText, appendUserMessage, fetchReply])

  const handleInputChange = useCallback((event) => {
    setInput(event.target.value)
    event.target.style.height = 'auto'
    event.target.style.height = `${Math.min(event.target.scrollHeight, 160)}px`
  }, [])

  const handleKeyDown = useCallback((event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      sendMessage()
    }
  }, [sendMessage])

  return {
    messages, input, isTyping, streamingId, textareaRef, loadingHistory,
    errorMessage, lastFailedText, sendMessage, stopGeneration, retry,
    dismissError: () => setErrorMessage(''), handleInputChange, handleKeyDown,
  }
}
