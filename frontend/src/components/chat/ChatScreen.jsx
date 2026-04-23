import { useCallback, useRef, useState } from 'react'
import { FileText, Loader2, Paperclip, Send, X } from 'lucide-react'
import ChatMessageBubble from '../ui/ChatMessageBubble'
import FileUploadPrompt from '../ui/FileUploadPrompt'
import ProcessingState from '../ui/ProcessingState'
import TypingIndicator from './TypingIndicator'
import ChatHeader from './ChatHeader'
import ChatSidebar from './ChatSidebar'
import useChat from '../../hooks/useChat'
import useAutoScroll from '../../hooks/useAutoScroll'

const rootClass = 'flex h-screen flex-col overflow-hidden bg-dm-background'
const bodyRowClass = 'flex min-h-0 flex-1 overflow-hidden'
const mainClass = 'flex min-h-0 flex-1 flex-col overflow-hidden bg-dm-background'
const messagesClass = 'flex-1 min-h-0 overflow-y-auto p-4 md:p-6'
const inputWrapClass =
  'flex shrink-0 items-center gap-3 border-t border-dm-border bg-dm-card p-4 md:px-6'
const inputClass =
  'flex-1 rounded-xl border border-dm-border bg-dm-background py-3 pl-12 pr-4 text-dm-foreground placeholder:text-dm-muted transition-shadow duration-200 focus:outline-none focus:ring-2 focus:ring-dm-primary focus:shadow-md focus:shadow-dm-primary/10 disabled:opacity-50 disabled:cursor-not-allowed'
const sendBtnClass =
  'shrink-0 rounded-lg p-2 text-dm-primary transition-all duration-150 hover:bg-dm-primary/10 hover:opacity-90 active:scale-95 disabled:opacity-40 disabled:pointer-events-none'
const errorBannerClass =
  'shrink-0 flex items-center gap-3 border-t border-red-500/20 bg-red-500/5 px-4 py-2.5'

const FILE_ACCEPT = '.pdf,.pptx,.png'

function ChatScreen({
  // conversations sidebar
  conversations = [],
  activeConversationId,
  onSelectConversation,
  onNewChat,
  onDeleteConversation,
  conversationsLoading = false,
  // files for the active (or in-flight) conversation
  files = [],
  onFirstUpload,
  onAddFile,
  onRemoveFile,
  uploadingFirstFileName = '',
  backTo = '/home',
  backLabel = 'Back to home',
}) {
  const {
    messages,
    status,
    isTyping,
    streamingId,
    loadingHistory,
    sendMessage,
    dismissError,
  } = useChat(activeConversationId)
  const [input, setInput] = useState('')
  const messagesRef = useRef(null)
  const fileInputRef = useRef(null)

  useAutoScroll(messagesRef, [messages, isTyping])

  const hasActive = Boolean(activeConversationId)
  const hasFilesProcessing = files.some((f) => f.status === 'processing')
  const isUploadingFirst = !hasActive && !!uploadingFirstFileName
  const isBusy = status === 'loading' || hasFilesProcessing || !!streamingId
  const sendDisabled = isBusy || loadingHistory

  const handleSend = (e) => {
    e.preventDefault()
    if (!input.trim() || isBusy) return
    sendMessage(input)
    setInput('')
  }

  const handlePaperclipClick = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const handleFileChange = useCallback(
    (e) => {
      const file = e.target.files?.[0]
      if (!file) return
      if (hasActive) onAddFile?.(file)
      else onFirstUpload?.(file)
      e.target.value = ''
    },
    [hasActive, onAddFile, onFirstUpload],
  )

  const placeholderText = hasFilesProcessing
    ? 'Processing document…'
    : streamingId
      ? 'Generating response…'
      : status === 'loading'
        ? 'Waiting for response…'
        : 'Chat with Docs'

  return (
    <div className={rootClass}>
      <input
        ref={fileInputRef}
        type="file"
        accept={FILE_ACCEPT}
        className="sr-only"
        aria-hidden
        onChange={handleFileChange}
      />

      <ChatHeader backTo={backTo} backLabel={backLabel} />

      <div className={bodyRowClass}>
        <ChatSidebar
          chats={conversations}
          activeId={activeConversationId}
          onSelectChat={onSelectConversation}
          onNewChat={onNewChat}
          onDeleteChat={onDeleteConversation}
          loading={conversationsLoading}
          emptyLabel="No past conversations yet."
        />

        <main className={mainClass}>
          {hasActive && files.length > 0 && (
            <div className="shrink-0 border-b border-dm-border px-4 py-2 md:px-6">
              <div className="flex flex-wrap items-center gap-2">
                {files.map((f) => (
                  <span
                    key={f.id}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-dm-border bg-dm-card px-3 py-1.5 text-sm"
                  >
                    {f.status === 'processing' ? (
                      <Loader2
                        size={14}
                        className="shrink-0 animate-spin text-dm-primary"
                      />
                    ) : (
                      <FileText size={14} className="shrink-0 text-dm-muted" />
                    )}
                    <span className="max-w-[180px] truncate text-dm-foreground">
                      {f.name}
                    </span>
                    {files.length > 1 && (
                      <button
                        type="button"
                        onClick={() => onRemoveFile?.(f.id)}
                        className="ml-0.5 shrink-0 rounded p-0.5 text-dm-muted hover:bg-dm-background hover:text-dm-foreground transition-colors"
                        aria-label={`Remove ${f.name}`}
                      >
                        <X size={14} />
                      </button>
                    )}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div ref={messagesRef} className={messagesClass}>
            {isUploadingFirst ? (
              <div className="flex h-full items-center justify-center">
                <ProcessingState fileName={uploadingFirstFileName} />
              </div>
            ) : !hasActive ? (
              <div className="flex h-full items-center justify-center px-4 py-8">
                <FileUploadPrompt
                  onFileSelect={onFirstUpload}
                  className="w-full max-w-2xl animate-fade-scale-in"
                />
              </div>
            ) : loadingHistory ? (
              <div className="flex h-full items-center justify-center gap-2 text-sm text-dm-muted">
                <Loader2 size={16} className="animate-spin" />
                Loading conversation…
              </div>
            ) : (
              <>
                {messages.map((m) => (
                  <ChatMessageBubble
                    key={m.id}
                    role={m.role}
                    text={m.text}
                    maxWidth="max-w-3xl"
                    streaming={m.id === streamingId}
                  />
                ))}
                {isTyping && <TypingIndicator maxWidth="max-w-3xl" />}
              </>
            )}
          </div>

          {status === 'error' && (
            <div className={errorBannerClass}>
              <p className="flex-1 text-sm text-red-400">
                Something went wrong. Please try again.
              </p>
              <button
                type="button"
                onClick={dismissError}
                className="text-sm font-medium text-red-400 hover:text-red-300 transition-colors"
              >
                Dismiss
              </button>
            </div>
          )}

          {hasActive && (
            <form onSubmit={handleSend} className={inputWrapClass}>
              <div className="relative flex flex-1 items-center">
                <button
                  type="button"
                  onClick={handlePaperclipClick}
                  className="absolute left-4 text-dm-muted hover:text-dm-primary transition-colors"
                  aria-label="Upload file"
                >
                  <Paperclip size={20} />
                </button>
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder={placeholderText}
                  className={inputClass}
                  disabled={sendDisabled}
                  aria-label="Message"
                />
              </div>
              <button
                type="submit"
                disabled={sendDisabled || !input.trim()}
                className={sendBtnClass}
                aria-label="Send"
              >
                <Send size={22} className="text-current" />
              </button>
            </form>
          )}
        </main>
      </div>
    </div>
  )
}

export default ChatScreen
