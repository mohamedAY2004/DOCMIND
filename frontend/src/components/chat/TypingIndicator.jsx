import { Brain } from 'lucide-react'

const dotClass = 'h-2 w-2 rounded-full bg-dm-primary/60'

function TypingIndicator({ maxWidth = 'max-w-3xl', showLabel = false }) {
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
        {showLabel && (
          <span className="text-xs font-medium text-dm-muted/60">
            Doc is typing&hellip;
          </span>
        )}
        <div className="flex items-center gap-1.5 rounded-xl bg-dm-card px-5 py-4 shadow-sm">
          <span className={`${dotClass} animate-typing-dot`} />
          <span className={`${dotClass} animate-typing-dot [animation-delay:160ms]`} />
          <span className={`${dotClass} animate-typing-dot [animation-delay:320ms]`} />
        </div>
      </div>
    </div>
  )
}

export default TypingIndicator
