import { useCallback, useLayoutEffect, useRef, useState } from 'react'
import { toast } from 'sonner'

/** Fetch one server page and discard responses superseded by filter/page changes. */
export default function usePageQuery(fetcher, params) {
  const key = JSON.stringify(params)
  const request = useRef(null)
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const refresh = useCallback(async () => {
    request.current?.abort()
    const controller = new AbortController()
    request.current = controller
    const owns = () => request.current === controller && !controller.signal.aborted
    setLoading(true)
    try {
      const response = await fetcher({ ...JSON.parse(key), signal: controller.signal })
      if (!owns()) return
      setItems(response.items)
      setTotal(response.total)
      setTotalPages(Math.max(1, response.totalPages))
    } catch (error) {
      if (owns()) toast.error(error.message || 'Could not load records.')
    } finally { if (owns()) setLoading(false) }
  }, [fetcher, key])
  useLayoutEffect(() => {
    void refresh()
    return () => { request.current?.abort(); request.current = null }
  }, [refresh])
  return { items, setItems, total, totalPages, loading, refresh }
}
