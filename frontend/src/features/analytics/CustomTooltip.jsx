const textColors = { '#22c55e': 'text-green-500', '#ef4444': 'text-red-500', '#0d6e73': 'text-dm-primary', '#a78bfa': 'text-violet-400' }

/**
 * Themed Recharts tooltip shared across the analytics diagrams.
 */
function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-xl border border-dm-border bg-dm-card px-4 py-3 shadow-xl">
      <p className="mb-1 text-xs font-medium text-dm-muted">{label}</p>
      {payload.map((p) => (
        <p key={p.dataKey} className={`text-sm ${textColors[p.color?.toLowerCase()] || 'text-dm-foreground'}`}>
          {p.name}: <span className="font-semibold">{p.value.toLocaleString()}</span>
        </p>
      ))}
    </div>
  )
}

export default CustomTooltip
