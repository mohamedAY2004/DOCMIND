import { useState, useRef, useEffect, useCallback } from 'react'
import { X, Bot, Send, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import ChatMessageBubble from '../ui/ChatMessageBubble'
import ErrorBanner from '../ui/ErrorBanner'
import TypingIndicator from './TypingIndicator'
import useAutoScroll from '../../hooks/useAutoScroll'
import { sendTestBotMessage } from '../../services/subjectService'

const backdropClass =
  'fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm transition-opacity'
const modalClass =
  'flex w-full max-w-3xl flex-col overflow-hidden rounded-card border border-dm-border bg-dm-card shadow-xl h-[80vh]'
const headerClass =
  'flex shrink-0 items-center justify-between gap-3 border-b border-dm-border bg-dm-card px-6 py-4'
const headerLeftClass = 'flex items-center gap-3 min-w-0'
const titleClass = 'text-lg font-bold text-dm-foreground'
const subjectClass = 'truncate text-sm text-dm-muted'
const closeBtnClass =
  'shrink-0 rounded-lg p-2 text-dm-muted hover:bg-dm-background hover:text-dm-foreground transition-colors'
const bodyClass = 'flex-1 min-h-0 overflow-y-auto px-6 py-4'
const noteClass = 'mb-4 text-sm text-dm-muted'
const inputWrapClass = 'flex shrink-0 items-center gap-3 border-t border-dm-border bg-dm-card p-4'
const inputClass =
  'flex-1 rounded-xl border border-dm-border bg-dm-background py-3 px-4 text-dm-foreground placeholder:text-dm-muted focus:outline-none focus:ring-2 focus:ring-dm-primary disabled:opacity-50 disabled:cursor-not-allowed'
const emptyStateClass =
  'flex flex-col items-center justify-center gap-3 h-full text-center px-4'

const MAX_MSG = 2000

/**
 * Return a user-friendly message from a service error.
 */
function friendlyError(err) {
  if (err?.code === 'ECONNABORTED' || err?.message?.includes('timeout')) {
    return 'The response took too long. The server may be under heavy load — please try again.'
  }
  if (!navigator.onLine) {
    return 'You appear to be offline. Check your connection and try again.'
  }
  const code = err?.response?.data?.code
  const serverMsg = err?.response?.data?.message
  if (code === 'SUBJECT_NOT_READY') {
    return serverMsg || 'No indexed materials yet. Upload a PDF and wait for processing.'
  }
  if (code === 'NOT_FOUND') return 'Subject not found.'
  if (serverMsg) return serverMsg
  const status = err?.response?.status
  if (status >= 500) return 'The server encountered an error. Please try again in a moment.'
  return 'Something went wrong. Please try again.'
}

function TestStudentBotModal({ isOpen, onClose, subjectName, subjectId }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [lastFailedText, setLastFailedText] = useState('')
  const messagesRef = useRef(null)
  const inputRef = useRef(null)
  useAutoScroll(messagesRef, [isOpen, messages, loading])

  // Reset conversation when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setMessages([])
      setInput('')
      setError('')
      setLastFailedText('')
      setLoading(false)
      // Focus input after mount
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }, [isOpen])

  // Escape key to close
  useEffect(() => {
    if (!isOpen) return
    const handleEsc = (e) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [isOpen, onClose])

  const doSend = useCallback(
    async (text) => {
      if (!text || loading) return
      if (text.length > MAX_MSG) {
        toast.error(`Message is too long. Max ${MAX_MSG} characters.`)
        return
      }

      setError('')
      setLastFailedText('')
      const userMsg = {
        id: `user-${Date.now()}`,
        role: 'user',
        text,
      }
      setMessages((prev) => [...prev, userMsg])
      setInput('')
      setLoading(true)

      try {
        const data = await sendTestBotMessage(subjectId, text)
        const botMsg = {
          id: `bot-${Date.now()}`,
          role: 'assistant',
          text: data.reply || 'No response received.',
        }
        setMessages((prev) => [...prev, botMsg])
        setLastFailedText('')
      } catch (err) {
        const errorText = friendlyError(err)
        setError(errorText)
        setLastFailedText(text)
        // Remove the optimistic user message so they can retry
        setMessages((prev) => prev.filter((m) => m.id !== userMsg.id))
      } finally {
        setLoading(false)
        setTimeout(() => inputRef.current?.focus(), 50)
      }
    },
    [loading, subjectId],
  )

  const handleSend = useCallback(
    (e) => {
      e.preventDefault()
      doSend(input.trim())
    },
    [input, doSend],
  )

  const handleRetry = useCallback(() => {
    if (lastFailedText) {
      setError('')
      doSend(lastFailedText)
    }
  }, [lastFailedText, doSend])

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) onClose()
  }

  if (!isOpen) return null

  const isEmpty = messages.length === 0 && !loading

  return (
    <div
      className={backdropClass}
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="test-bot-modal-title"
    >
      <div className={modalClass} onClick={(e) => e.stopPropagation()}>
        <header className={headerClass}>
          <div className={headerLeftClass}>
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-dm-primary/15">
              <Bot size={20} className="shrink-0 text-dm-primary" />
            </div>
            <div className="min-w-0">
              <h2 id="test-bot-modal-title" className={titleClass}>
                Test Student Bot
              </h2>
              <p className={subjectClass}>{subjectName}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className={closeBtnClass}
            aria-label="Close modal"
          >
            <X size={22} className="text-current" />
          </button>
        </header>

        <div ref={messagesRef} className={bodyClass}>
          {isEmpty ? (
            <div className={emptyStateClass}>
              <div className="flex h-20 w-20 items-center justify-center rounded-full bg-dm-primary/10">
                <Bot size={40} className="text-dm-primary" strokeWidth={1.5} />
              </div>
              <p className="text-lg font-semibold text-dm-foreground">
                Test your bot
              </p>
              <p className="max-w-sm text-sm text-dm-muted">
                Send a question below to preview how students will interact with
                the AI tutor based on your uploaded materials.
              </p>
            </div>
          ) : (
            <>
              <p className={noteClass}>
                This is a live preview — responses are generated from your
                indexed materials. No history is saved.
              </p>
              {messages.map((m) => (
                <ChatMessageBubble
                  key={m.id}
                  role={m.role}
                  text={m.text}
                  variant="modal"
                />
              ))}
              {loading && <TypingIndicator maxWidth="max-w-2xl" />}
            </>
          )}
        </div>

        {error && (
          <ErrorBanner
            message={error}
            icon
            onRetry={lastFailedText ? handleRetry : undefined}
            onDismiss={() => { setError(''); setLastFailedText('') }}
          />
        )}

        <form onSubmit={handleSend} className={inputWrapClass}>
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              loading ? 'Generating response…' : 'Ask a question as a student…'
            }
            className={inputClass}
            aria-label="Message"
            disabled={loading}
            maxLength={MAX_MSG + 200}
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="shrink-0 rounded-lg p-2 text-dm-primary hover:bg-dm-primary/10 transition-all duration-150 active:scale-95 disabled:opacity-40 disabled:pointer-events-none"
            aria-label="Send"
          >
            {loading ? (
              <Loader2 size={24} className="animate-spin text-dm-primary" />
            ) : (
              <Send size={24} className="text-current" />
            )}
          </button>
        </form>
      </div>
    </div>
  )
}

export default TestStudentBotModal
