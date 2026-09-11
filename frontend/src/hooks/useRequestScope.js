import { useCallback, useLayoutEffect, useRef } from 'react'

/** A lifetime for requests whose results belong to one selected resource. */
export default function useRequestScope(key) {
  const current = useRef(null)
  const reset = useCallback(() => {
    current.current?.abort()
    current.current = new AbortController()
  }, [])
  useLayoutEffect(() => {
    reset()
    return () => { current.current?.abort(); current.current = null }
  }, [key, reset])
  const capture = useCallback(() => {
    const controller = current.current
    return { signal: controller?.signal,
      owns: () => Boolean(controller && current.current === controller && !controller.signal.aborted) }
  }, [])
  return { capture, reset }
}
