import { useEffect } from 'react'

/**
 * Scrolls the element attached to scrollRef to bottom when deps change.
 * @param {React.MutableRefObject<HTMLElement | null>} scrollRef - Ref on the scrollable container
 * @param {React.DependencyList} deps - Dependencies (e.g. [messages])
 */
function useAutoScroll(scrollRef, deps) {
  useEffect(() => {
    const el = scrollRef.current
    if (!el) return
    el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
}

export default useAutoScroll
