import { useMemo, useRef, useState, useEffect } from 'react'
import { Check, ChevronDown, Search, X } from 'lucide-react'
import { primaryChipActiveClass } from '../../constants/themeClasses'

/**
 * Tailwind-styled multi-select with checkbox rows + a pill preview.
 *
 * options: Array<{ id: string, label: string, sub?: string }>
 * value:   Array<string>
 * onChange(next: Array<string>)
 */
function MultiSelect({
  options = [],
  value = [],
  onChange,
  placeholder = 'Select…',
  emptyLabel = 'No options',
  disabled = false,
}) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const rootRef = useRef(null)

  useEffect(() => {
    if (!open) return
    const onClick = (e) => {
      if (rootRef.current && !rootRef.current.contains(e.target)) {
        setOpen(false)
      }
    }
    const onKey = (e) => {
      if (e.key === 'Escape') setOpen(false)
    }
    window.addEventListener('mousedown', onClick)
    window.addEventListener('keydown', onKey)
    return () => {
      window.removeEventListener('mousedown', onClick)
      window.removeEventListener('keydown', onKey)
    }
  }, [open])

  const byId = useMemo(() => {
    const m = new Map()
    options.forEach((o) => m.set(o.id, o))
    return m
  }, [options])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return options
    return options.filter(
      (o) =>
        o.label.toLowerCase().includes(q) ||
        (o.sub || '').toLowerCase().includes(q) ||
        o.id.toLowerCase().includes(q),
    )
  }, [options, query])

  const toggle = (id) => {
    if (value.includes(id)) {
      onChange?.(value.filter((v) => v !== id))
    } else {
      onChange?.([...value, id])
    }
  }

  const remove = (id) => {
    onChange?.(value.filter((v) => v !== id))
  }

  const selected = value.map((id) => byId.get(id)).filter(Boolean)

  return (
    <div className="relative" ref={rootRef}>
      <button
        type="button"
        onClick={() => !disabled && setOpen((v) => !v)}
        disabled={disabled}
        className={`flex min-h-[42px] w-full flex-wrap items-center gap-1.5 rounded-xl border border-dm-border bg-dm-background px-3 py-2 text-left text-sm text-dm-foreground transition-colors focus:outline-none focus:ring-2 focus:ring-dm-primary/40 ${
          disabled ? 'cursor-not-allowed opacity-60' : 'hover:border-dm-primary/40'
        }`}
      >
        {selected.length === 0 && (
          <span className="text-dm-muted">{placeholder}</span>
        )}
        {selected.map((o) => (
          <span
            key={o.id}
            className="flex items-center gap-1 rounded-full bg-dm-primary/15 px-2 py-0.5 text-xs font-medium text-dm-primary"
          >
            {o.label}
            {!disabled && (
              <span
                role="button"
                tabIndex={-1}
                onClick={(e) => {
                  e.stopPropagation()
                  remove(o.id)
                }}
                className="rounded-full p-0.5 hover:bg-dm-primary/20"
              >
                <X size={10} />
              </span>
            )}
          </span>
        ))}
        <ChevronDown
          size={16}
          className={`ml-auto text-dm-muted transition-transform ${open ? 'rotate-180' : ''}`}
        />
      </button>

      {open && (
        <div className="absolute z-20 mt-1 w-full overflow-hidden rounded-xl border border-dm-border bg-dm-card shadow-2xl">
          <div className="relative border-b border-dm-border/60">
            <Search
              size={14}
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-dm-muted"
            />
            <input
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search…"
              className="w-full bg-transparent py-2.5 pl-9 pr-3 text-sm text-dm-foreground placeholder:text-dm-muted focus:outline-none"
            />
          </div>
          <div className="max-h-60 overflow-y-auto">
            {filtered.length === 0 ? (
              <p className="px-3 py-4 text-center text-xs text-dm-muted">
                {emptyLabel}
              </p>
            ) : (
              filtered.map((o) => {
                const checked = value.includes(o.id)
                return (
                  <button
                    key={o.id}
                    type="button"
                    onClick={() => toggle(o.id)}
                    className={`flex w-full items-center justify-between gap-3 px-3 py-2 text-left text-sm transition-colors hover:bg-dm-background ${
                      checked ? 'text-dm-foreground' : 'text-dm-muted'
                    }`}
                  >
                    <div className="min-w-0">
                      <p className="truncate">{o.label}</p>
                      {o.sub && (
                        <p className="truncate text-[11px] text-dm-muted">{o.sub}</p>
                      )}
                    </div>
                    <span
                      className={`flex h-4 w-4 shrink-0 items-center justify-center rounded border ${
                        checked
                          ? `border-dm-primary ${primaryChipActiveClass}`
                          : 'border-dm-border'
                      }`}
                    >
                      {checked && <Check size={12} />}
                    </span>
                  </button>
                )
              })
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default MultiSelect
