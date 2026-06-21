import { useCallback, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import { GraduationCap, Loader2, Lock, Send } from 'lucide-react'
import ChatMessageBubble from '../ui/ChatMessageBubble'
import ErrorBanner from '../ui/ErrorBanner'
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
  sendMessageFeedback,
  clearMessageFeedback,
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
function TutorChatScreen({ subjectId, subjectName, semesterState = 'active' }) {
  const [feedbackMap, setFeedbackMap] = useState({})

  // Past/future terms are read-only: students can browse and re-read history
  // (the GET paths gate on ownership, not semester) but cannot start new turns.
  const readOnly = semesterState !== 'active'
  const readOnlyReason =
    semesterState === 'archived'
      ? 'This semester is archived — you can review past conversations, but starting new chats is disabled.'
      : 'This semester hasn’t started yet — the tutor will open once it begins.'

  const handleFeedback = useCallback(async (messageId, value) => {
    const prev = feedbackMap[messageId] ?? null
    setFeedbackMap((m) => ({ ...m, [messageId]: value }))
    try {
      if (value === null) {
        await clearMessageFeedback(messageId)
      } else {
        await sendMessageFeedback(messageId, value)
      }
    } catch {
      setFeedbackMap((m) => ({ ...m, [messageId]: prev }))
      toast.error('Could not save feedback.')
    }
  }, [feedbackMap])

  const handleFeedbackMapLoaded = useCallback((loaded) => {
    setFeedbackMap(loaded)
  }, [])

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
    onFeedbackMapLoaded: handleFeedbackMapLoaded,
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
          disableNewChat={readOnly}
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
                    variant="tutor"
                    streaming={m.id === streamingId}
                    messageId={m.role === 'assistant' ? m.id : undefined}
                    feedbackValue={m.role === 'assistant' ? (feedbackMap[m.id] ?? null) : undefined}
                    onFeedback={m.role === 'assistant' ? handleFeedback : undefined}
                  />
                ))}
                {isTyping && <TypingIndicator maxWidth="max-w-3xl" />}
              </>
            )}
          </div>

          {errorMessage && (
            <ErrorBanner
              message={errorMessage}
              onRetry={lastFailedText ? retry : undefined}
              onDismiss={dismissError}
            />
          )}

          <div className="shrink-0 border-t border-dm-border bg-dm-card">
            {readOnly ? (
              <div className="flex items-center gap-2.5 px-4 py-4 text-sm text-dm-muted md:px-6">
                <Lock size={16} className="shrink-0 text-amber-400" />
                <span>{readOnlyReason}</span>
              </div>
            ) : (
              <>
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
              </>
            )}
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
