import { useRef, useEffect } from 'react'
import { X, Bot, Send, Square } from 'lucide-react'
import { toast } from 'sonner'
import ChatMessageBubble from '../ui/ChatMessageBubble'
import ErrorBanner from '../ui/ErrorBanner'
import TypingIndicator from './TypingIndicator'
import useAutoScroll from '../../hooks/useAutoScroll'
import usePreviewChat from '../../hooks/usePreviewChat'
import useScopedDraft from '../../hooks/useScopedDraft'

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

function TestStudentBotModal({ isOpen, onClose, subjectName, subjectId }) {
  const { messages, isTyping, streamingId, errorMessage: error, lastFailedText,
    sendMessage, stopGeneration, retry: handleRetry, dismissError } = usePreviewChat(subjectId, isOpen)
  const [input, setInput] = useScopedDraft(`${subjectId}:${isOpen}`)
  const loading = isTyping || Boolean(streamingId)
  const messagesRef = useRef(null)
  const inputRef = useRef(null)
  const modalRef = useRef(null)
  useAutoScroll(messagesRef, [isOpen, messages, loading])

  // Trap focus and support Escape while the modal is open.
  useEffect(() => {
    if (!isOpen) return
    const previous = document.activeElement
    const handleKey = (event) => {
      if (event.key === 'Escape') onClose()
      if (event.key !== 'Tab') return
      const items = [...(modalRef.current?.querySelectorAll('button,textarea,[tabindex]:not([tabindex="-1"])') || [])]
      if (!items.length) return
      const first = items[0]
      const last = items[items.length - 1]
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus() }
      if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
    }
    window.addEventListener('keydown', handleKey)
    return () => {
      window.removeEventListener('keydown', handleKey)
      previous?.focus?.()
    }
  }, [isOpen, onClose])

  const doSend = (text) => {
    if (!text || loading) return
    if (text.length > MAX_MSG) { toast.error(`Message is too long. Max ${MAX_MSG} characters.`); return }
    void sendMessage(text)
    setInput('')
  }
  const handleSend = (event) => { event.preventDefault(); doSend(input.trim()) }

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
      <div ref={modalRef} className={modalClass} onClick={(e) => e.stopPropagation()}>
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
                  streaming={m.generationStatus === 'generating'}
                  citations={m.citations}
                  groundingStatus={m.groundingStatus}
                  generationStatus={m.generationStatus}
                />
              ))}
              {loading && !messages.at(-1)?.text && <TypingIndicator maxWidth="max-w-2xl" />}
            </>
          )}
        </div>

        {error && (
          <ErrorBanner
            message={error}
            icon
            onRetry={lastFailedText ? handleRetry : undefined}
            onDismiss={dismissError}
          />
        )}

        <form onSubmit={handleSend} className={inputWrapClass}>
          <textarea
            ref={inputRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey && !loading) {
                event.preventDefault()
                doSend(input.trim())
              }
            }}
            placeholder={
              loading ? 'Generating response…' : 'Ask a question as a student…'
            }
            className={inputClass}
            aria-label="Message"
            disabled={loading}
            maxLength={MAX_MSG + 200}
          />
          <button
            type={loading ? 'button' : 'submit'}
            onClick={loading ? stopGeneration : undefined}
            disabled={!loading && !input.trim()}
            className="shrink-0 rounded-lg p-2 text-dm-primary hover:bg-dm-primary/10 transition-all duration-150 active:scale-95 disabled:opacity-40 disabled:pointer-events-none"
            aria-label={loading ? 'Stop generating' : 'Send'}
          >
            {loading ? (
              <Square size={20} className="fill-current text-dm-primary" />
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
