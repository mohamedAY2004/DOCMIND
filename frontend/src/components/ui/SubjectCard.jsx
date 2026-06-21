import { useLayoutEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { primarySurfaceClass } from '../../constants/themeClasses'

const cardClass = [
  'group flex flex-col rounded-card border border-dm-border bg-dm-card p-6 md:p-8',
  'shadow-lg shadow-black/20',
  'transition-all duration-300 ease-out',
  'hover:-translate-y-1 hover:shadow-xl hover:shadow-dm-primary/10 hover:border-dm-primary/40',
].join(' ')

const titleClass = 'text-lg font-bold text-dm-foreground'
const badgeBaseClass =
  'shrink-0 rounded-full px-2.5 py-0.5 text-[11px] font-semibold ring-1 whitespace-nowrap'

// Visual treatment per derived semester state. 'active' shows no badge.
const STATE_BADGE = {
  archived: { label: 'Archived', cls: 'bg-amber-500/15 text-amber-400 ring-amber-500/30' },
  upcoming: { label: 'Upcoming', cls: 'bg-sky-500/15 text-sky-400 ring-sky-500/30' },
}
const descClass = 'mt-2 text-sm leading-relaxed text-dm-muted'
const descClampClass = 'line-clamp-3'
const toggleClass =
  'mt-1 self-start text-xs font-semibold text-dm-primary transition-colors hover:text-dm-primary/80 focus:outline-none focus-visible:underline'
const buttonWrapClass = 'mt-auto pt-6'

const buttonStyleClass = [
  primarySurfaceClass,
  'flex w-full items-center justify-center gap-2 rounded-xl py-3 px-4',
  'transition-all duration-300',
  'group-hover:shadow-lg group-hover:shadow-dm-primary/30 group-hover:scale-[1.02] group-hover:brightness-110',
].join(' ')

const arrowClass =
  'inline-block transition-transform duration-300 ease-out group-hover:translate-x-1'

function SubjectCard({
  title,
  description,
  buttonText = 'Start Chatting →',
  href,
  className = '',
  semesterState = 'active',
}) {
  const badge = STATE_BADGE[semesterState]
  const descRef = useRef(null)
  const [expanded, setExpanded] = useState(false)
  const [isOverflowing, setIsOverflowing] = useState(false)

  // Detect whether the clamped description is actually truncated so the
  // "Show more" toggle only appears for genuinely long descriptions.
  useLayoutEffect(() => {
    if (expanded) return
    const el = descRef.current
    if (!el) return
    const check = () => setIsOverflowing(el.scrollHeight > el.clientHeight + 1)
    check()
    window.addEventListener('resize', check)
    return () => window.removeEventListener('resize', check)
  }, [description, expanded])

  const hasArrow = buttonText.includes('→')
  const cleanText = hasArrow ? buttonText.replace('→', '').trim() : buttonText

  const buttonContent = (
    <>
      <span>{cleanText}</span>
      {hasArrow && <span className={arrowClass}>→</span>}
    </>
  )

  return (
    <div className={[cardClass, className].filter(Boolean).join(' ')}>
      <div className="flex items-start justify-between gap-3">
        <h3 className={titleClass}>{title}</h3>
        {badge && (
          <span className={`${badgeBaseClass} ${badge.cls}`}>{badge.label}</span>
        )}
      </div>
      {description && (
        <>
          <p
            ref={descRef}
            title={description}
            className={`${descClass} ${expanded ? '' : descClampClass}`}
          >
            {description}
          </p>
          {(isOverflowing || expanded) && (
            <button
              type="button"
              onClick={() => setExpanded((v) => !v)}
              className={toggleClass}
              aria-expanded={expanded}
            >
              {expanded ? 'Show less' : 'Show more'}
            </button>
          )}
        </>
      )}
      <div className={buttonWrapClass}>
        {href ? (
          <Link to={href} className={buttonStyleClass}>
            {buttonContent}
          </Link>
        ) : (
          <span className={buttonStyleClass}>{buttonContent}</span>
        )}
      </div>
    </div>
  )
}

export default SubjectCard
