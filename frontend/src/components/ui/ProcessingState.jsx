import { useState, useEffect, useRef } from 'react'

const STATUSES = [
  'Uploading file…',
  'Processing content…',
  'Analyzing document…',
  'Preparing chat…',
]

const R = 52
const CIRCUMFERENCE = 2 * Math.PI * R
const TICK_MS = 30

function ProcessingState({ durationMs = 4000, fileName = '' }) {
  const [progress, setProgress] = useState(0)
  const [statusIdx, setStatusIdx] = useState(0)
  const [textVisible, setTextVisible] = useState(true)
  const stepRef = useRef(100 / (durationMs / TICK_MS))

  useEffect(() => {
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
  }, [])

  useEffect(() => {
    const interval = durationMs / STATUSES.length
    const id = setInterval(() => {
      setTextVisible(false)
      setTimeout(() => {
        setStatusIdx((i) => (i + 1) % STATUSES.length)
        setTextVisible(true)
      }, 180)
    }, interval)
    return () => clearInterval(id)
  }, [durationMs])

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
    </div>
  )
}

export default ProcessingState
