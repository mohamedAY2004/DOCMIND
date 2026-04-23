import { useState, useRef, useEffect } from 'react'
import { X, Bot, Send } from 'lucide-react'
import ChatMessageBubble from '../ui/ChatMessageBubble'
import useAutoScroll from '../../hooks/useAutoScroll'

const SAMPLE_MESSAGES = [
  {
    id: '1',
    role: 'assistant',
    text: "Hello! I'm the student bot for this subject. Ask me anything about the materials you've uploaded.",
  },
  {
    id: '2',
    role: 'user',
    text: 'What are the main topics in the first lecture?',
  },
  {
    id: '3',
    role: 'assistant',
    text: 'Based on the uploaded materials, the first lecture covers an introduction to the core concepts, including definitions and key terminology. I can go into more detail on any section you specify.',
  },
]

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
  'flex-1 rounded-xl border border-dm-border bg-dm-background py-3 px-4 text-dm-foreground placeholder:text-dm-muted focus:outline-none focus:ring-2 focus:ring-dm-primary'

function TestStudentBotModal({ isOpen, onClose, subjectName }) {
  const [messages, setMessages] = useState(SAMPLE_MESSAGES)
  const [input, setInput] = useState('')
  const messagesEndRef = useRef(null)
  useAutoScroll(messagesEndRef, [isOpen, messages])

  useEffect(() => {
    if (!isOpen) return
    const handleEsc = (e) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [isOpen, onClose])

  const handleSend = (e) => {
    e.preventDefault()
    const text = input.trim()
    if (!text) return
    setMessages((prev) => [...prev, { id: String(Date.now()), role: 'user', text }])
    setInput('')
  }

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) onClose()
  }

  if (!isOpen) return null

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
            <Bot size={24} className="shrink-0 text-dm-primary" />
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

        <div ref={messagesEndRef} className={bodyClass}>
          <p className={noteClass}>
            This is a preview of how students will interact with your bot.
          </p>
          {messages.map((m) => (
            <ChatMessageBubble key={m.id} role={m.role} text={m.text} variant="modal" />
          ))}
        </div>

        <form onSubmit={handleSend} className={inputWrapClass}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message..."
            className={inputClass}
            aria-label="Message"
          />
          <button
            type="submit"
            className="shrink-0 rounded-lg p-2 text-dm-primary hover:bg-dm-background transition-colors"
            aria-label="Send"
          >
            <Send size={24} className="text-current" />
          </button>
        </form>
      </div>
    </div>
  )
}

export default TestStudentBotModal
