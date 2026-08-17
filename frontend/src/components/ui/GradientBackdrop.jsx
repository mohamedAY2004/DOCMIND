const PRESETS = {
  default:
    'bg-[radial-gradient(ellipse_60%_50%_at_50%_40%,rgb(var(--dm-primary)/0.15)_0%,transparent_70%)]',
  subtle:
    'bg-[radial-gradient(ellipse_55%_45%_at_50%_45%,rgb(var(--dm-primary)/0.12)_0%,transparent_70%)]',
  cards:
    'bg-[radial-gradient(ellipse_60%_55%_at_50%_55%,rgb(var(--dm-primary)/0.12)_0%,transparent_70%)]',
  corner:
    'bg-[radial-gradient(circle_at_30%_20%,rgb(var(--dm-primary)/0.1)_0%,transparent_40%)]',
  chat:
    'bg-[radial-gradient(ellipse_70%_50%_at_50%_40%,rgb(var(--dm-primary)/0.08)_0%,transparent_70%)]',
  vignette:
    'bg-[radial-gradient(ellipse_100%_100%_at_50%_50%,transparent_55%,var(--dm-backdrop-vignette)_100%)]',
}

function GradientBackdrop({ variant = 'default', gradient, className = '' }) {
  const presetClass = PRESETS[variant] || PRESETS.default

  return (
    <div
      className={`pointer-events-none absolute inset-0 ${gradient ? '' : presetClass} ${className}`}
      aria-hidden
      style={gradient ? { background: gradient } : undefined}
    />
  )
}

export default GradientBackdrop
