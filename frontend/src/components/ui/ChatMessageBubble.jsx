import { useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import { Brain, User, Copy, Check } from 'lucide-react'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import { primarySurfaceClassBr } from '../../constants/themeClasses'

const bubbleUserAddClass = 'flex-row-reverse ml-auto'

const assistantInnerDefaultClass =
  'rounded-xl bg-dm-card p-4 text-dm-foreground shadow-sm transition-shadow duration-200 hover:shadow-md'
const assistantInnerModalClass =
  'rounded-xl border border-dm-border bg-dm-background p-4 text-dm-foreground transition-shadow duration-200 hover:shadow-md'
const assistantInnerTutorClass =
  'rounded-xl bg-gradient-to-br from-dm-card via-dm-card/90 to-dm-card/70 border border-dm-border/30 p-4 text-dm-foreground shadow-md shadow-dm-primary/5 transition-all duration-200 hover:shadow-lg hover:shadow-dm-primary/10'
const bubbleUserInnerClass =
  `${primarySurfaceClassBr} rounded-xl p-4 transition-shadow duration-200 hover:shadow-lg hover:shadow-dm-primary/30`

const actionBtnBase =
  'flex h-7 w-7 items-center justify-center rounded-md transition-all duration-150 hover:bg-dm-background'
const actionBtnHidden = 'opacity-0 group-hover:opacity-100'

const remarkPlugins = [remarkGfm]
const rehypePlugins = [rehypeHighlight]

const VARIANT_INNER = {
  default: assistantInnerDefaultClass,
  modal: assistantInnerModalClass,
  tutor: assistantInnerTutorClass,
}

const bubbleVariants = {
  hidden: { opacity: 0, y: 12, scale: 0.97 },
  visible: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.3, ease: 'easeOut' } },
}

function StreamingCursor() {
  return (
    <span className="inline-block align-middle ml-0.5">
      <span className="inline-block h-2.5 w-2.5 rounded-full bg-dm-primary animate-pulse" />
    </span>
  )
}

function ChatMessageBubble({
  role,
  text,
  maxWidth = 'max-w-2xl',
  variant = 'default',
  streaming = false,
}) {
  const isAssistant = role === 'assistant' || role === 'doc'
  const [copied, setCopied] = useState(false)

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      toast.success('Copied to clipboard')
      setTimeout(() => setCopied(false), 1500)
    })
  }, [text])

  const innerClass = isAssistant
    ? VARIANT_INNER[variant] || assistantInnerDefaultClass
    : bubbleUserInnerClass
  const isTutor = variant === 'tutor'
  const Icon = isAssistant ? Brain : User

  return (
    <motion.div
      variants={bubbleVariants}
      initial="hidden"
      animate="visible"
      className={`group flex gap-3 mb-4 ${maxWidth} ${!isAssistant ? bubbleUserAddClass : ''}`.trim()}
    >
      {isTutor ? (
        <div
          className={`mt-0.5 shrink-0 flex h-8 w-8 items-center justify-center rounded-full ${
            isAssistant
              ? 'bg-dm-primary/10 ring-2 ring-dm-primary/20'
              : 'bg-dm-primary/20 ring-2 ring-dm-primary/30'
          }`}
        >
          <Icon
            size={16}
            className={
              isAssistant ? 'text-dm-primary' : 'text-dm-primary'
            }
          />
        </div>
      ) : (
        <Icon
          size={24}
          className={`mt-1 shrink-0 ${isAssistant ? 'text-dm-primary' : 'text-dm-primary'}`}
        />
      )}
      <div className="flex flex-col gap-1 min-w-0">
        <div className={innerClass}>
          {isAssistant ? (
            <div className="chat-prose prose prose-sm max-w-none">
              <Markdown
                remarkPlugins={remarkPlugins}
                rehypePlugins={rehypePlugins}
              >
                {text}
              </Markdown>
              {streaming && <StreamingCursor />}
            </div>
          ) : (
            <div className="whitespace-pre-wrap text-white">
              {text}
            </div>
          )}
        </div>
        {isAssistant && !streaming && (
          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={handleCopy}
              className={`${actionBtnBase} ${copied ? '' : actionBtnHidden} ${copied ? 'text-dm-primary' : 'text-dm-muted hover:text-dm-foreground'}`}
              aria-label={copied ? 'Copied' : 'Copy response'}
            >
              {copied ? <Check size={14} /> : <Copy size={14} />}
            </button>
          </div>
        )}
      </div>
    </motion.div>
  )
}

export default ChatMessageBubble
