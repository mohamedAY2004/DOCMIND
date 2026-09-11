import { useCallback, useLayoutEffect, useRef, useState } from 'react'
import { toast } from 'sonner'

/** Paginated conversation list. Fetchers accept {page, signal}; scope changes
 * revoke every pending read and mutation's permission to update this list. */
export default function useConversations({ fetcher, remover, updater, signalKey = null, autoSelectFirst = false }) {
  const [conversations, setConversations] = useState([])
  const [selectionVersion, setSelectionVersion] = useState(0)
  const [activeId, setActiveId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [hasMore, setHasMore] = useState(false)
  const ownerRef = useRef(null)
  const pageRef = useRef(0)
  const readRef = useRef(null)
  const mutations = useRef(new Map())

  const load = useCallback(async (owner, page) => {
    readRef.current?.abort()
    const controller = new AbortController()
    readRef.current = controller
    const revision = owner.revision
    const owns = () => ownerRef.current === owner && readRef.current === controller
    setLoading(true)
    try {
      const response = await fetcher({ page, signal: controller.signal })
      if (!owns()) return
      const changes = [...owner.changes.entries()].filter(([, change]) => change.revision > revision)
      let items = response.items
      for (const [id, change] of changes) {
        items = change.value === null ? items.filter((item) => item.id !== id)
          : items.map((item) => item.id === id ? { ...item, ...change.value } : item)
        if (page === 1 && change.created && !items.some((item) => item.id === id)) items = [change.value, ...items]
      }
      setConversations((previous) => page === 1 ? items
        : [...previous, ...items.filter((item) => !previous.some((old) => old.id === item.id))])
      setHasMore(response.page < response.totalPages)
      if (autoSelectFirst && pageRef.current === 0 && !owner.selectionChanged) setActiveId((id) => id ?? items[0]?.id ?? null)
      pageRef.current = response.page
    } catch {
      if (owns()) toast.error('Could not load conversation history.')
    } finally {
      if (owns()) { readRef.current = null; setLoading(false) }
    }
  }, [fetcher, autoSelectFirst])

  useLayoutEffect(() => {
    const owner = { revision: 0, changes: new Map(), selectionChanged: false }
    ownerRef.current = owner
    pageRef.current = 0
    mutations.current.clear()
    setConversations([])
    setActiveId(null)
    setHasMore(false)
    void load(owner, 1)
    return () => { ownerRef.current = null; readRef.current?.abort(); readRef.current = null }
  }, [signalKey, load])

  const mutate = useCallback(async (id, operation, apply, success) => {
    const owner = ownerRef.current
    const token = {}
    mutations.current.set(id, token)
    const owns = () => ownerRef.current === owner && mutations.current.get(id) === token
    try {
      await operation()
      if (!owns()) return
      apply()
      toast.success(success)
    } catch {
      if (owns()) toast.error('Could not update the conversation.')
    } finally {
      if (owns()) mutations.current.delete(id)
    }
  }, [])

  const selectConversation = useCallback((id) => {
    if (ownerRef.current) ownerRef.current.selectionChanged = true
    setSelectionVersion((version) => version + 1); setActiveId(id ?? null)
  }, [])
  const startNewConversation = useCallback(() => selectConversation(null), [selectConversation])
  const recordChange = useCallback((id, value, created = false) => {
    const owner = ownerRef.current
    if (owner) {
      const previous = owner.changes.get(id)
      owner.changes.set(id, {
        value: value === null ? null : { ...previous?.value, ...value },
        created: created || Boolean(previous?.created), revision: ++owner.revision,
      })
    }
  }, [])
  const prependConversation = useCallback((conversation) => {
    if (!conversation?.id) return
    recordChange(conversation.id, conversation, true)
    setConversations((previous) => [conversation, ...previous.filter((item) => item.id !== conversation.id)])
    setActiveId(conversation.id)
  }, [recordChange])
  const updateConversation = useCallback((id, patch) => {
    recordChange(id, patch)
    setConversations((previous) => previous.map((item) => item.id === id ? { ...item, ...patch } : item))
  }, [recordChange])
  const deleteConversation = useCallback((id) => remover && mutate(id, () => remover(id), () => {
    recordChange(id, null)
    setConversations((previous) => previous.filter((item) => item.id !== id))
    setActiveId((current) => current === id ? null : current)
  }, 'Conversation deleted.'), [remover, mutate, recordChange])
  const renameConversation = useCallback((id, title) => updater && mutate(id, () => updater(id, title), () => {
    updateConversation(id, { title })
  }, 'Conversation renamed.'), [updater, mutate, updateConversation])

  return { conversations, activeId, selectionVersion, loading, hasMore,
    refresh: () => ownerRef.current && load(ownerRef.current, 1),
    loadMore: () => !readRef.current && hasMore && ownerRef.current && load(ownerRef.current, pageRef.current + 1),
    selectConversation, startNewConversation, prependConversation, updateConversation,
    deleteConversation, renameConversation, setActiveId }
}
