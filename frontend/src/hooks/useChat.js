import { useCallback, useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'
import { getDocMessages, sendDocMessage } from '../services/chatService'
import useStreamingText from './useStreamingText'

const WELCOME = {
  id: 'welcome',
  role: 'doc',
  text: "Hello! I'm Doc, your AI academic assistant. Let's get started!",
}

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
  if (code === 'FILES_NOT_READY') {
    return 'Your documents are still being processed. Please wait a moment and try again.'
  }
  if (code === 'VALIDATION_ERROR') {
    return err?.response?.data?.message || 'Invalid request. Please check your message.'
  }
  const status = err?.response?.status
  if (status >= 500) {
    return 'The server encountered an error. Please try again in a moment.'
  }
  return 'Something went wrong. Please try again.'
}

/**
 * Doc-chat hook — rendering layer for a specific `conversationId` created via
 * `createDocConversation`. The backend owns message persistence; the hook
 * pulls stored history on conversation change and layers optimistic local
 * updates on top while new replies stream in.
 */
export default function useChat(conversationId) {
  const [messages, setMessages] = useState([WELCOME])
  const [status, setStatus] = useState('idle')
  const [isTyping, setIsTyping] = useState(false)
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [lastFailedText, setLastFailedText] = useState('')
  const busyRef = useRef(false)

  const handleStreamComplete = useCallback(() => {
    setStatus('idle')
    busyRef.current = false
  }, [])

  const { streamingId, streamReply, stopStreaming } = useStreamingText(
    setMessages,
    handleStreamComplete,
  )

  // Load stored history when switching conversations. A `null` id means
  // we're sitting on a brand-new (not-yet-persisted) chat, so just reset.
  useEffect(() => {
    stopStreaming()
    busyRef.current = false
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setStatus('idle')
    setIsTyping(false)
    setErrorMessage('')
    setLastFailedText('')

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
        if (cancelled) return
        if (items.length === 0) {
          setMessages([WELCOME])
          return
        }
        setMessages(
          items.map((m) => ({
            id: m.id,
            role: m.role === 'user' ? 'user' : 'doc',
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

  const sendMessage = useCallback(
    async (text) => {
      const trimmed = text.trim()
      if (!trimmed || busyRef.current) return
      if (!conversationId) {
        setStatus('error')
        setErrorMessage('No active conversation. Please upload a document first.')
        return
      }

      busyRef.current = true
      setErrorMessage('')
      setLastFailedText('')
      const tempId = `user-${Date.now()}`
      setMessages((prev) => [
        ...prev,
        { id: tempId, role: 'user', text: trimmed },
      ])
      setStatus('loading')
      setIsTyping(true)

      try {
        const { userMessage, reply } = await sendDocMessage(
          conversationId,
          trimmed,
        )

        setMessages((prev) =>
          prev.map((m) =>
            m.id === tempId && userMessage?.id
              ? { ...m, id: userMessage.id }
              : m,
          ),
        )

        const msgId = reply?.id || `doc-${Date.now()}`
        const replyText = reply?.text || ''
        setMessages((prev) => [
          ...prev,
          { id: msgId, role: 'doc', text: '' },
        ])
        setIsTyping(false)
        streamReply(replyText, msgId)
      } catch (err) {
        const msg = friendlyError(err)
        setStatus('error')
        setErrorMessage(msg)
        setLastFailedText(trimmed)
        busyRef.current = false
        setIsTyping(false)
        // Remove the optimistic user message so the UI stays clean
        setMessages((prev) => prev.filter((m) => m.id !== tempId))
      }
    },
    [conversationId, streamReply],
  )

  const retry = useCallback(() => {
    if (lastFailedText) {
      setErrorMessage('')
      setStatus('idle')
      sendMessage(lastFailedText)
    }
  }, [lastFailedText, sendMessage])

  const resetChat = useCallback(() => {
    stopStreaming()
    busyRef.current = false
    setMessages([WELCOME])
    setStatus('idle')
    setIsTyping(false)
    setErrorMessage('')
    setLastFailedText('')
  }, [stopStreaming])

  const dismissError = useCallback(() => {
    if (status === 'error') {
      setStatus('idle')
      setErrorMessage('')
    }
  }, [status])

  return {
    messages,
    status,
    isTyping,
    streamingId,
    loadingHistory,
    errorMessage,
    lastFailedText,
    sendMessage,
    retry,
    resetChat,
    dismissError,
  }
}
