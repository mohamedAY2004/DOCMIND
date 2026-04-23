import { useCallback, useRef, useState } from 'react'

const STREAM_INTERVAL_MS = 30

export default function useStreamingText(setMessages, onComplete) {
  const [streamingId, setStreamingId] = useState(null)
  const intervalRef = useRef(null)

  const streamReply = useCallback((fullText, msgId) => {
    let charIndex = 0
    setStreamingId(msgId)

    intervalRef.current = setInterval(() => {
      const nextChunk = Math.min(charIndex + 2 + Math.floor(Math.random() * 3), fullText.length)
      charIndex = nextChunk

      setMessages((prev) =>
        prev.map((m) => (m.id === msgId ? { ...m, text: fullText.slice(0, nextChunk) } : m)),
      )

      if (charIndex >= fullText.length) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
        setStreamingId(null)
        onComplete?.()
      }
    }, STREAM_INTERVAL_MS)
  }, [setMessages, onComplete])

  const stopStreaming = useCallback(() => {
    if (intervalRef.current) clearInterval(intervalRef.current)
    intervalRef.current = null
    setStreamingId(null)
  }, [])

  return { streamingId, streamReply, stopStreaming }
}
