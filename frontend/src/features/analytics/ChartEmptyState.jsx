/**
 * Centered placeholder shown inside a chart card when no data matches the
 * diagram's current filters.
 */
function ChartEmptyState({ icon: Icon, message, heightClass = 'h-[300px]' }) {
  return (
    <div className={`flex flex-col items-center justify-center gap-2 ${heightClass}`}>
      {Icon ? <Icon size={32} className="text-dm-muted/40" /> : null}
      <p className="text-sm text-dm-muted">{message}</p>
    </div>
  )
}

export default ChartEmptyState
