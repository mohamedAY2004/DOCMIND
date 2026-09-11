import { useLayoutEffect, useRef } from 'react'

/** Preserve the visible history when prepending; follow new replies at the end. */
export default function useMessageScroll(scrollRef, messages, isTyping, conversationId) {
  const previous = useRef(null)
  useLayoutEffect(() => {
    const element = scrollRef.current
    if (!element) return
    const old = previous.current
    const prepended = old?.conversationId === conversationId && old.firstId
      && messages[0]?.id !== old.firstId && messages.some((message) => message.id === old.firstId)
    if (prepended) element.scrollTop += element.scrollHeight - old.height
    else element.scrollTo({ top: element.scrollHeight, behavior: 'auto' })
    previous.current = { conversationId, firstId: messages[0]?.id, height: element.scrollHeight }
  }, [scrollRef, messages, isTyping, conversationId])
}
