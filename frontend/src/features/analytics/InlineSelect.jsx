import { ChevronDown } from 'lucide-react'

/**
 * Compact dropdown used inside chart card headers for per-diagram filtering.
 */
function InlineSelect({ icon: Icon, value, onChange, ariaLabel, children }) {
  return (
    <div className="relative">
      {Icon ? (
        <Icon
          size={13}
          className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-dm-muted"
        />
      ) : null}
      <select
        aria-label={ariaLabel}
        value={value}
        onChange={onChange}
        className={`cursor-pointer appearance-none rounded-lg border border-dm-border bg-dm-background py-1.5 pr-7 text-xs font-medium text-dm-foreground transition-colors hover:border-dm-primary/40 focus:outline-none focus:ring-2 focus:ring-dm-primary/40 ${Icon ? 'pl-7' : 'pl-3'}`}
      >
        {children}
      </select>
      <ChevronDown
        size={13}
        className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-dm-muted"
      />
    </div>
  )
}

export default InlineSelect
