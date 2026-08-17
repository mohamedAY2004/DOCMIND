import { useCallback, useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'
import { cancelMessage, getDocMessages, streamDocMessage } from '../services/chatService'

const WELCOME = {
  id: 'welcome', role: 'doc',
  text: "Hello! I'm Doc, your AI academic assistant. Let's get started!",
  citations: [], generationStatus: 'complete',
}

function friendlyError(err) {
  if (err?.name === 'AbortError') return 'The response was stopped. You can retry it.'
  if (!navigator.onLine) return 'You appear to be offline. Please check your connection and try again.'
  const code = err?.response?.data?.code
  if (code === 'FILES_NOT_READY') return 'Your documents are still being processed. Please wait a moment and try again.'
  if (code === 'VALIDATION_ERROR') return err?.response?.data?.message || 'Invalid request.'
  if (err?.response?.status >= 500) return 'The server encountered an error. Please try again in a moment.'
  return err?.message || 'Something went wrong. Please try again.'
}

function normalizeMessage(message, assistantRole = 'doc') {
  return {
    ...message,
    role: message.role === 'user' ? 'user' : assistantRole,
    text: message.text ?? '',
    citations: message.citations ?? [],
    generationStatus: message.generationStatus ?? 'complete',
    groundingStatus: message.groundingStatus ?? null,
  }
}

export default function useChat(conversationId) {
  const [messages, setMessages] = useState([WELCOME])
  const [status, setStatus] = useState('idle')
  const [isTyping, setIsTyping] = useState(false)
  const [streamingId, setStreamingId] = useState(null)
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [lastFailedText, setLastFailedText] = useState('')
  const busyRef = useRef(false)
  const controllerRef = useRef(null)
  const replyIdRef = useRef(null)

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
    setStatus('idle')
    busyRef.current = false
  }, [])

  useEffect(() => {
    controllerRef.current?.abort()
    controllerRef.current = null
    replyIdRef.current = null
    busyRef.current = false
    setStatus('idle')
    setStreamingId(null)
    setIsTyping(false)
    setErrorMessage('')
    setLastFailedText('')
    replyIdRef.current = null
    if (!conversationId) {
      setMessages([WELCOME])
      setLoadingHistory(false)
      return
    }
    let cancelled = false
    setMessages([WELCOME])
    setLoadingHistory(true)
    getDocMessages(conversationId)
      .then((items) => {
        if (!cancelled) setMessages(items.length ? items.map((m) => normalizeMessage(m)) : [WELCOME])
      })
      .catch(() => { if (!cancelled) toast.error('Could not load this conversation.') })
      .finally(() => { if (!cancelled) setLoadingHistory(false) })
    return () => { cancelled = true }
  }, [conversationId])

  const sendMessage = useCallback(async (text) => {
    const trimmed = text.trim()
    if (!trimmed || busyRef.current) return
    if (!conversationId) {
      setStatus('error')
      setErrorMessage('No active conversation. Please upload a document first.')
      return
    }
    busyRef.current = true
    setStatus('loading')
    setIsTyping(true)
    setErrorMessage('')
    setLastFailedText('')
    const tempId = `user-${Date.now()}`
    setMessages((prev) => [...prev, { id: tempId, role: 'user', text: trimmed }])
    const controller = new AbortController()
    controllerRef.current = controller

    try {
      await streamDocMessage(conversationId, trimmed, {
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
            setStatus('streaming')
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
            if (reply.generationStatus === 'cancelled') setLastFailedText(trimmed)
          } else if (event === 'answer.failed') {
            setMessages((prev) => prev.map((m) => (
              m.id === payload.replyId ? { ...m, generationStatus: 'failed' } : m
            )))
            setErrorMessage(payload.message || 'Generation failed.')
            setLastFailedText(trimmed)
            setStatus('error')
          }
        },
      })
      setStatus((current) => (current === 'error' ? current : 'idle'))
    } catch (err) {
      setErrorMessage(friendlyError(err))
      setLastFailedText(trimmed)
      setStatus(err?.name === 'AbortError' ? 'idle' : 'error')
      if (!replyIdRef.current) setMessages((prev) => prev.filter((m) => m.id !== tempId))
    } finally {
      if (controllerRef.current === controller) controllerRef.current = null
      setStreamingId(null)
      setIsTyping(false)
      busyRef.current = false
    }
  }, [conversationId])

  const retry = useCallback(() => {
    if (!lastFailedText) return
    const text = lastFailedText
    setLastFailedText('')
    setErrorMessage('')
    setStatus('idle')
    sendMessage(text)
  }, [lastFailedText, sendMessage])

  const dismissError = useCallback(() => {
    setErrorMessage('')
    if (status === 'error') setStatus('idle')
  }, [status])

  return {
    messages, status, isTyping, streamingId, loadingHistory, errorMessage,
    lastFailedText, sendMessage, stopGeneration, retry, dismissError,
  }
}
