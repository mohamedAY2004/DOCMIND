import { useCallback, useRef } from 'react'
import { motion } from 'framer-motion'
import { GraduationCap, Loader2, RefreshCw, Send } from 'lucide-react'
import ChatMessageBubble from '../ui/ChatMessageBubble'
import TypingIndicator from './TypingIndicator'
import ChatHeader from './ChatHeader'
import ChatSidebar from './ChatSidebar'
import useAutoScroll from '../../hooks/useAutoScroll'
import useConversations from '../../hooks/useConversations'
import useTutorChat from '../../hooks/useTutorChat'
import {
  deleteTutorConversation,
  updateTutorConversation,
  listTutorConversations,
} from '../../services/chatService'

const MAX_MSG = 2000

const rootClass = 'flex h-screen flex-col overflow-hidden bg-dm-background'
const bodyRowClass = 'flex min-h-0 flex-1 overflow-hidden'
const mainClass = 'flex min-h-0 flex-1 flex-col overflow-hidden bg-dm-background'
const bannerClass =
  'shrink-0 border-b border-dm-border px-4 py-3 text-sm text-dm-muted md:px-6'
const messagesClass = 'flex-1 min-h-0 overflow-y-auto p-4 md:p-6'
const inputWrapClass =
  'flex shrink-0 items-end gap-3 border-t border-dm-border bg-dm-card p-4 md:px-6'
const textareaClass =
  'flex-1 resize-none rounded-xl border border-dm-border bg-dm-background py-3 px-4 text-dm-foreground placeholder:text-dm-muted transition-shadow duration-200 focus:outline-none focus:ring-2 focus:ring-dm-primary focus:shadow-md focus:shadow-dm-primary/10 disabled:opacity-50'
const sendBtnClass =
  'shrink-0 rounded-lg p-2 text-dm-primary transition-all duration-150 hover:bg-dm-primary/10 hover:opacity-90 active:scale-95 disabled:opacity-40 disabled:pointer-events-none'
const errorBannerClass =
  'shrink-0 flex items-center gap-3 border-t border-red-500/20 bg-red-500/5 px-4 py-2.5'

function TutorChatScreen({ subjectId, subjectName }) {
  const fetcher = useCallback(
    () => listTutorConversations(subjectId),
    [subjectId],
  )

  const {
    conversations,
    activeId,
    loading: conversationsLoading,
    selectConversation,
    startNewConversation,
    prependConversation,
    deleteConversation,
    renameConversation,
  } = useConversations({
    fetcher,
    remover: deleteTutorConversation,
    updater: updateTutorConversation,
    signalKey: subjectId,
    autoSelectFirst: true,
  })

  const handleConversationCreated = useCallback(
    (conv) => {
      if (!conv?.id) return
      prependConversation({
        id: conv.id,
        title: conv.title || 'New chat',
        subjectId: conv.subjectId ?? subjectId,
        updatedAt: conv.updatedAt,
      })
    },
    [prependConversation, subjectId],
  )

  const {
    messages,
    input,
    isTyping,
    streamingId,
    textareaRef,
    loadingHistory,
    errorMessage,
    lastFailedText,
    sendMessage,
    retry,
    dismissError,
    handleInputChange,
    handleKeyDown,
  } = useTutorChat({
    subjectId,
    conversationId: activeId,
    onConversationCreated: handleConversationCreated,
  })

  const messagesRef = useRef(null)
  useAutoScroll(messagesRef, [messages, isTyping])

  const handleNewChat = useCallback(() => {
    startNewConversation()
  }, [startNewConversation])

  const hasUserMessages = messages.some((m) => m.role === 'user')
  const isBusy = isTyping || !!streamingId
  const showWelcome = !loadingHistory && !hasUserMessages && !isTyping
  const msgTooLong = input.length > MAX_MSG

  return (
    <div className={rootClass}>
      <ChatHeader backTo="/tutors" backLabel="Back to tutors" />

      <div className={bodyRowClass}>
        <ChatSidebar
          chats={conversations}
          activeId={activeId}
          onSelectChat={selectConversation}
          onNewChat={handleNewChat}
          onDeleteChat={deleteConversation}
          onRenameChat={renameConversation}
          loading={conversationsLoading}
          emptyLabel="No past conversations yet."
        />

        <main className={mainClass}>
          <div className={bannerClass}>Subject: {subjectName}</div>

          <div ref={messagesRef} className={messagesClass}>
            {loadingHistory ? (
              <div className="flex h-full items-center justify-center gap-2 text-sm text-dm-muted">
                <Loader2 size={16} className="animate-spin" />
                Loading conversation…
              </div>
            ) : showWelcome ? (
              <WelcomeState subjectName={subjectName} />
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

          {/* Error banner with retry */}
          {errorMessage && (
            <div className={errorBannerClass}>
              <p className="flex-1 text-sm text-red-400">{errorMessage}</p>
              <div className="flex items-center gap-2">
                {lastFailedText && (
                  <button
                    type="button"
                    onClick={retry}
                    className="flex items-center gap-1.5 rounded-md bg-red-500/10 px-3 py-1.5 text-sm font-medium text-red-400 hover:bg-red-500/20 transition-colors"
                  >
                    <RefreshCw size={14} />
                    Retry
                  </button>
                )}
                <button
                  type="button"
                  onClick={dismissError}
                  className="text-sm font-medium text-red-400 hover:text-red-300 transition-colors"
                >
                  Dismiss
                </button>
              </div>
            </div>
          )}

          <div className="shrink-0 border-t border-dm-border bg-dm-card">
            {msgTooLong && (
              <p className="px-4 pt-2 text-xs text-red-400">
                Message is too long. Please shorten it to under {MAX_MSG} characters.
              </p>
            )}
            <form onSubmit={sendMessage} className={inputWrapClass}>
              <textarea
                ref={textareaRef}
                value={input}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder={
                  isBusy
                    ? streamingId
                      ? 'Generating response…'
                      : 'Waiting for response…'
                    : `Ask about ${subjectName}…`
                }
                disabled={isBusy || loadingHistory}
                rows={1}
                className={`${textareaClass} ${msgTooLong ? 'border-red-500/60 focus:ring-red-500/20' : ''}`}
                aria-label="Message"
                maxLength={MAX_MSG + 200}
              />
              {input.length > MAX_MSG * 0.8 && (
                <span className={`shrink-0 self-end pb-2 text-xs tabular-nums ${msgTooLong ? 'text-red-400' : 'text-dm-muted'}`}>
                  {input.length}/{MAX_MSG}
                </span>
              )}
              <button
                type="submit"
                disabled={isBusy || loadingHistory || !input.trim() || msgTooLong}
                className={sendBtnClass}
                aria-label="Send"
              >
                {isTyping ? (
                  <Loader2 size={22} className="animate-spin text-dm-primary" />
                ) : (
                  <Send size={22} className="text-current" />
                )}
              </button>
            </form>
          </div>
        </main>
      </div>
    </div>
  )
}

function WelcomeState({ subjectName }) {
  return (
    <motion.div
      className="flex h-full flex-col items-center justify-center text-center"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
    >
      <motion.div
        className="flex h-16 w-16 items-center justify-center rounded-2xl bg-dm-primary/10 mb-5 ring-2 ring-dm-primary/20 shadow-lg shadow-dm-primary/10"
        initial={{ scale: 0.8 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.1, type: 'spring', stiffness: 200 }}
      >
        <GraduationCap size={32} className="text-dm-primary" />
      </motion.div>
      <h2 className="text-xl font-bold text-dm-foreground mb-2">
        Welcome to your AI Tutor
      </h2>
      <p className="text-sm text-dm-muted/70 max-w-md">
        Ask anything about{' '}
        <span className="text-dm-primary font-medium">{subjectName}</span>{' '}
        materials
      </p>
    </motion.div>
  )
}

export default TutorChatScreen
