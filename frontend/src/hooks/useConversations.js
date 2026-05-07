import { useCallback, useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'

/**
 * Generic conversation-list controller used by both the doc and tutor
 * chat surfaces. It owns:
 *
 *   • `conversations` — the currently loaded list (server order).
 *   • `activeId`       — which conversation is open. `null` means the user
 *                        is starting a brand-new chat that has not been
 *                        persisted yet.
 *
 * Callers pass a `fetcher(signalKey?)` that returns the list and a
 * `remover(id)` that deletes server-side. The hook handles toasts,
 * cancellation on unmount, optimistic deletion, and prepending newly
 * created conversations.
 */
export default function useConversations({
  fetcher,
  remover,
  updater,
  signalKey = null,
  autoSelectFirst = false,
}) {
  const [conversations, setConversations] = useState([])
  const [activeId, setActiveId] = useState(null)
  const [loading, setLoading] = useState(true)
  const loadedOnceRef = useRef(false)

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const items = await fetcher(signalKey)
      const list = Array.isArray(items) ? items : []
      setConversations(list)
      if (autoSelectFirst && !loadedOnceRef.current && list[0]?.id) {
        setActiveId(list[0].id)
      }
      loadedOnceRef.current = true
      return list
    } catch {
      toast.error('Could not load conversation history.')
      return []
    } finally {
      setLoading(false)
    }
  }, [fetcher, signalKey, autoSelectFirst])

  useEffect(() => {
    loadedOnceRef.current = false
    refresh()
  }, [refresh])

  const selectConversation = useCallback((id) => {
    setActiveId(id ?? null)
  }, [])

  const startNewConversation = useCallback(() => {
    setActiveId(null)
  }, [])

  const prependConversation = useCallback((conv) => {
    if (!conv?.id) return
    setConversations((prev) => {
      if (prev.some((c) => c.id === conv.id)) return prev
      return [conv, ...prev]
    })
    setActiveId(conv.id)
  }, [])

  const updateConversation = useCallback((id, patch) => {
    setConversations((prev) =>
      prev.map((c) => (c.id === id ? { ...c, ...patch } : c)),
    )
  }, [])

  const deleteConversation = useCallback(
    async (id) => {
      if (!remover) return
      const snapshot = conversations
      setConversations((prev) => prev.filter((c) => c.id !== id))
      if (activeId === id) setActiveId(null)
      try {
        await remover(id)
        toast.success('Conversation deleted.')
      } catch {
        setConversations(snapshot)
        toast.error('Could not delete the conversation.')
      }
    },
    [conversations, activeId, remover],
  )

  const renameConversation = useCallback(
    async (id, title) => {
      if (!updater) return
      
      // Optimistic update
      const previous = conversations.find(c => c.id === id)
      updateConversation(id, { title })
      
      try {
        await updater(id, title)
        toast.success('Conversation renamed.')
      } catch {
        // Revert on error
        if (previous) {
          updateConversation(id, { title: previous.title })
        }
        toast.error('Could not rename the conversation.')
      }
    },
    [conversations, updater, updateConversation],
  )

  return {
    conversations,
    activeId,
    loading,
    refresh,
    selectConversation,
    startNewConversation,
    prependConversation,
    updateConversation,
    deleteConversation,
    renameConversation,
    setActiveId,
  }
}
