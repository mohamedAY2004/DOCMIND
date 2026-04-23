import { useCallback, useEffect, useRef, useState } from 'react'

/**
 * Small async-fetch helper that tracks loading / error / data state and
 * respects unmounts. The caller passes a stable `fn` (memoised with
 * `useCallback` when it closes over props) and an optional `deps` array that
 * re-runs the fetch when those inputs change.
 *
 * The hook also exposes a `refresh()` method and a `setData()` setter so
 * pages can optimistically mutate the cached value (e.g. after a PATCH).
 */
export default function useAsync(fn, deps = []) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const cancelledRef = useRef(false)

  const run = useCallback(async () => {
    cancelledRef.current = false
    setLoading(true)
    setError(null)
    try {
      const result = await fn()
      if (cancelledRef.current) return
      setData(result)
    } catch (err) {
      if (cancelledRef.current) return
      setError(err)
    } finally {
      if (!cancelledRef.current) setLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  useEffect(() => {
    run()
    return () => {
      cancelledRef.current = true
    }
  }, [run])

  return { data, error, loading, refresh: run, setData }
}
