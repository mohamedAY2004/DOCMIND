import { useEffect, useState } from 'react'
import { Brain } from 'lucide-react'

const dotClass = 'h-2 w-2 rounded-full bg-dm-primary/60'

/**
 * Time thresholds (ms) at which we show increasingly informative messages
 * so the user knows the system is alive even during slow LLM generation.
 */
const SLOW_THRESHOLD_MS = 6_000
const VERY_SLOW_THRESHOLD_MS = 20_000

const SLOW_MESSAGES = [
  'Thinking deeply…',
  'Still working on it…',
  'Almost there…',
  'Generating a thorough response…',
]

function TypingIndicator({ maxWidth = 'max-w-3xl', showLabel = false }) {
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    const start = Date.now()
    const id = setInterval(() => setElapsed(Date.now() - start), 1000)
    return () => clearInterval(id)
  }, [])

  const isSlow = elapsed >= SLOW_THRESHOLD_MS
  const isVerySlow = elapsed >= VERY_SLOW_THRESHOLD_MS

  // Pick a rotating message when slow
  const slowIdx = Math.floor(elapsed / 5000) % SLOW_MESSAGES.length
  const statusText = isVerySlow
    ? `Still generating… ${Math.floor(elapsed / 1000)}s`
    : isSlow
      ? SLOW_MESSAGES[slowIdx]
      : showLabel
        ? 'Doc is typing\u2026'
        : null

  return (
    <div className={`flex gap-3 mb-4 ${maxWidth} animate-message-in`}>
      {showLabel ? (
        <div className="mt-0.5 shrink-0 flex h-8 w-8 items-center justify-center rounded-full bg-dm-primary/10 ring-2 ring-dm-primary/20">
          <Brain size={16} className="text-dm-primary" />
        </div>
      ) : (
        <Brain size={24} className="mt-1 shrink-0 text-dm-primary" />
      )}
      <div className="flex flex-col gap-1.5">
        {statusText && (
          <span className="text-xs font-medium text-dm-muted/60 transition-opacity duration-300">
            {statusText}
          </span>
        )}
        <div className="flex items-center gap-1.5 rounded-xl bg-dm-card px-5 py-4 shadow-sm">
          <span className={`${dotClass} animate-typing-dot`} />
          <span className={`${dotClass} animate-typing-dot [animation-delay:160ms]`} />
          <span className={`${dotClass} animate-typing-dot [animation-delay:320ms]`} />
          {isSlow && (
            <span className="ml-2 text-xs text-dm-muted/50 tabular-nums">
              {Math.floor(elapsed / 1000)}s
            </span>
          )}
        </div>
      </div>
    </div>
  )
}

export default TypingIndicator
