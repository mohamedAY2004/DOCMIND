import { streamTestBotMessage } from '../services/subjectService'
import useChatSession from './useChatSession'

const adapter = {
  role: 'assistant', welcome: [], cancel: async () => {},
  stream: (subjectId, text, { onEvent, ...options }) => streamTestBotMessage(subjectId, text, {
    ...options,
    onEvent: (event, payload) => onEvent(event, event === 'message.created'
      ? { ...payload, userMessage: { id: `preview-user-${crypto.randomUUID()}`, role: 'user', text } }
      : payload),
  }),
}

export default function usePreviewChat(subjectId, isOpen) {
  return useChatSession({ conversationId: isOpen ? subjectId : null, adapter })
}
