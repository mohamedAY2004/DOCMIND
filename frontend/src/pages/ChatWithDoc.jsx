import ChatScreen from '../components/chat/ChatScreen'
import useConversations from '../hooks/useConversations'
import useDocumentFiles from '../hooks/useDocumentFiles'
import { deleteDocConversation, updateDocConversation, listDocConversations } from '../services/chatService'

export default function ChatWithDoc() {
  const list = useConversations({ fetcher: listDocConversations,
    remover: deleteDocConversation, updater: updateDocConversation })
  const attachments = useDocumentFiles(list.activeId, list.prependConversation)
  return <ChatScreen
    conversations={list.conversations}
    activeConversationId={list.activeId}
    onSelectConversation={(id) => { if (id !== list.activeId) { attachments.reset(); list.selectConversation(id) } }}
    onNewChat={() => { attachments.reset(); list.startNewConversation() }}
    onDeleteConversation={list.deleteConversation}
    onRenameConversation={list.renameConversation}
    conversationsLoading={list.loading}
    hasMoreConversations={list.hasMore}
    loadMoreConversations={list.loadMore}
    files={attachments.files}
    onFirstUpload={attachments.upload}
    onAddFile={attachments.upload}
    onRemoveFile={attachments.remove}
    uploadingFirstFileName={attachments.uploadingFirstFileName}
  />
}
