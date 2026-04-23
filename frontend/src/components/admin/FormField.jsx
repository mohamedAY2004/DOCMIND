function FormField({ label, required, hint, error, children }) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="flex items-center gap-1 text-[11px] font-medium uppercase tracking-wider text-dm-muted">
        {label}
        {required && <span className="text-red-400">*</span>}
      </span>
      {children}
      {hint && !error && <span className="text-[11px] text-dm-muted">{hint}</span>}
      {error && <span className="text-[11px] text-red-400">{error}</span>}
    </label>
  )
}

export const inputClass =
  'w-full rounded-xl border border-dm-border bg-dm-background px-3 py-2.5 text-sm text-dm-foreground placeholder:text-dm-muted transition-colors focus:border-dm-primary/40 focus:outline-none focus:ring-2 focus:ring-dm-primary/30 disabled:opacity-60'

export const textareaClass = `${inputClass} min-h-[96px] resize-y`

export const selectClass =
  'w-full appearance-none rounded-xl border border-dm-border bg-dm-background px-3 py-2.5 text-sm text-dm-foreground transition-colors focus:border-dm-primary/40 focus:outline-none focus:ring-2 focus:ring-dm-primary/30 disabled:opacity-60'

export default FormField
