import { useRef } from 'react'
import { createTutorConversation, getTutorMessages, streamTutorMessage } from '../services/chatService'
import useChatSession from './useChatSession'
import useScopedDraft from './useScopedDraft'

const adapter = { history: getTutorMessages, stream: streamTutorMessage,
  create: createTutorConversation, role: 'assistant', welcome: [] }

export default function useTutorChat({ subjectId, conversationId, selectionVersion, onConversationCreated, onFeedbackMapLoaded }) {
  const [input, setInput] = useScopedDraft(`${subjectId}:${conversationId ?? ''}:${selectionVersion}`)
  const textareaRef = useRef(null)
  const feedback = useRef({})
  const session = useChatSession({ conversationId, scopeId: subjectId, resetKey: selectionVersion, adapter, onConversationCreated,
    onHistoryLoaded(items, reset) {
      if (reset) feedback.current = {}
      for (const message of items) {
        if (message.role !== 'user' && message.feedback) feedback.current[message.id] = message.feedback
      }
      onFeedbackMapLoaded?.({ ...feedback.current })
    },
  })
  const sendMessage = (event) => {
    event?.preventDefault()
    if (!input.trim() || session.isTyping || session.streamingId || session.loadingHistory) return
    void session.sendMessage(input)
    setInput('')
  }
  return { ...session, input, textareaRef, sendMessage,
    handleInputChange: (event) => setInput(event.target.value),
    handleKeyDown: (event) => {
      if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); sendMessage() }
    },
  }
}
