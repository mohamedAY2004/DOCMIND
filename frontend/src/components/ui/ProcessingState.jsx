import { useState, useEffect, useRef } from 'react'

const STATUSES = [
  'Uploading file…',
  'Processing content…',
  'Analyzing document…',
  'Preparing chat…',
  'Indexing pages…',
  'Almost ready…',
]

const R = 52
const CIRCUMFERENCE = 2 * Math.PI * R
const TICK_MS = 30

/**
 * Visual processing indicator. When `indefinite` is true the progress ring
 * slows down asymptotically toward 95 % and never stops — it waits for the
 * caller to unmount or set a different state. This is ideal for server-side
 * processing where we don't know the real duration.
 */
function ProcessingState({
  durationMs = 4000,
  fileName = '',
  indefinite = false,
}) {
  const [progress, setProgress] = useState(0)
  const [statusIdx, setStatusIdx] = useState(0)
  const [textVisible, setTextVisible] = useState(true)
  const [elapsed, setElapsed] = useState(0)
  const startRef = useRef(Date.now())
  const stepRef = useRef(100 / (durationMs / TICK_MS))

  // Elapsed seconds counter
  useEffect(() => {
    const id = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startRef.current) / 1000))
    }, 1000)
    return () => clearInterval(id)
  }, [])

  // Progress animation
  useEffect(() => {
    if (indefinite) {
      // Asymptotic: fast at first, slows as it approaches 95 %
      const id = setInterval(() => {
        setProgress((p) => {
          if (p >= 95) return 95
          // Remaining distance shrinks so the bar decelerates
          const remaining = 95 - p
          return p + remaining * 0.015
        })
      }, TICK_MS)
      return () => clearInterval(id)
    }

    const id = setInterval(() => {
      setProgress((p) => {
        const next = p + stepRef.current
        if (next >= 100) {
          clearInterval(id)
          return 100
        }
        return next
      })
    }, TICK_MS)
    return () => clearInterval(id)
  }, [indefinite])

  // Cycling status text
  useEffect(() => {
    const interval = indefinite
      ? Math.max(3000, durationMs / STATUSES.length)
      : durationMs / STATUSES.length
    const id = setInterval(() => {
      setTextVisible(false)
      setTimeout(() => {
        setStatusIdx((i) => (i + 1) % STATUSES.length)
        setTextVisible(true)
      }, 180)
    }, interval)
    return () => clearInterval(id)
  }, [durationMs, indefinite])

  const dashOffset = CIRCUMFERENCE - (progress / 100) * CIRCUMFERENCE

  return (
    <div className="flex flex-col items-center gap-8 animate-fade-scale-in">
      {/* Circular progress */}
      <div className="relative flex items-center justify-center">
        {/* Pulsing glow behind ring */}
        <div
          className="absolute inset-[-12px] rounded-full bg-dm-primary/15 blur-xl animate-pulse-glow"
          aria-hidden
        />

        <svg width="136" height="136" viewBox="0 0 136 136" className="relative -rotate-90">
          {/* Track */}
          <circle
            cx="68"
            cy="68"
            r={R}
            fill="none"
            strokeWidth="5"
            className="stroke-dm-border"
          />
          {/* Progress arc */}
          <circle
            cx="68"
            cy="68"
            r={R}
            fill="none"
            strokeWidth="5"
            strokeLinecap="round"
            className="stroke-dm-primary"
            style={{
              strokeDasharray: CIRCUMFERENCE,
              strokeDashoffset: dashOffset,
              transition: `stroke-dashoffset ${TICK_MS + 10}ms ease-out`,
            }}
          />
        </svg>

        {/* Percentage in center */}
        <span className="absolute text-2xl font-bold tabular-nums text-dm-foreground">
          {Math.round(progress)}%
        </span>
      </div>

      {/* Cycling status text */}
      <p
        className={`h-7 text-lg text-dm-muted text-center max-w-xs transition-opacity duration-200 ease-in-out ${textVisible ? 'opacity-100' : 'opacity-0'}`}
      >
        {STATUSES[statusIdx]}
      </p>

      {/* File name */}
      {fileName && (
        <p className="max-w-xs truncate text-sm text-dm-muted/60">{fileName}</p>
      )}

      {/* Elapsed time — shown after 5 seconds so the user knows the system is alive */}
      {elapsed >= 5 && (
        <p className="text-xs text-dm-muted/40 tabular-nums animate-fade-in">
          {elapsed}s elapsed
        </p>
      )}
    </div>
  )
}

export default ProcessingState
