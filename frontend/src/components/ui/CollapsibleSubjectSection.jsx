import { useState } from 'react'
import { ChevronDown } from 'lucide-react'

// Badge treatment per derived semester state, mirroring SubjectCard.jsx.
// 'active' gets a subtle "Current" pill so the live term is easy to spot.
const STATE_BADGE = {
  active: { label: 'Current', cls: 'bg-emerald-500/15 text-emerald-400 ring-emerald-500/30' },
  archived: { label: 'Archived', cls: 'bg-amber-500/15 text-amber-400 ring-amber-500/30' },
  upcoming: { label: 'Upcoming', cls: 'bg-sky-500/15 text-sky-400 ring-sky-500/30' },
}
const badgeBaseClass =
  'shrink-0 rounded-full px-2.5 py-0.5 text-[11px] font-semibold ring-1 whitespace-nowrap'

/**
 * One collapsible semester section. Header toggles the body open/closed; the
 * card grid is passed as `children` so each page keeps rendering its own card.
 *
 * The collapse is a pure-CSS `grid-template-rows: 0fr→1fr` transition rather than
 * a framer-motion height animation. The content stays mounted (just clipped), so
 * cards in an initially-open section render immediately and lay out at full width
 * — animating height in JS mis-measured the grid while the cards were also doing
 * `layout` animations, leaving them blank/narrow until a reopen.
 */
function CollapsibleSubjectSection({
  title,
  state,
  count,
  defaultOpen = false,
  children,
}) {
  const [open, setOpen] = useState(defaultOpen)
  const badge = STATE_BADGE[state]

  return (
    <section className="mt-8 first:mt-10">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full items-center gap-3 rounded-xl border border-dm-border/60 bg-dm-card/40 px-4 py-3 text-left transition-colors duration-200 hover:bg-dm-card/70"
      >
        <ChevronDown
          size={18}
          className={`shrink-0 text-dm-muted transition-transform duration-200 ${open ? '' : '-rotate-90'}`}
        />
        <h2 className="text-lg font-bold text-dm-foreground">{title}</h2>
        {badge && <span className={`${badgeBaseClass} ${badge.cls}`}>{badge.label}</span>}
        <span className="ml-auto text-sm font-medium text-dm-muted">
          {count} {count === 1 ? 'subject' : 'subjects'}
        </span>
      </button>

      <div
        className={`grid transition-[grid-template-rows] duration-300 ease-out ${
          open ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'
        }`}
      >
        <div className="overflow-hidden">
          <div className="pt-6">{children}</div>
        </div>
      </div>
    </section>
  )
}

export default CollapsibleSubjectSection
