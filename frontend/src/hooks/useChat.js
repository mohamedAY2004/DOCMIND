import { getDocMessages, streamDocMessage } from '../services/chatService'
import useChatSession from './useChatSession'

const adapter = {
  history: getDocMessages,
  stream: streamDocMessage,
  role: 'doc',
  welcome: [{ id: 'welcome', role: 'doc', text: "Hello! I'm Doc, your AI academic assistant. Let's get started!",
    citations: [], generationStatus: 'complete' }],
}

export default function useChat(conversationId) {
  return useChatSession({ conversationId, adapter })
}
