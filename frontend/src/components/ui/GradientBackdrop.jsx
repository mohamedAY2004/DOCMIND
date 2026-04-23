const PRESETS = {
  default:
    'radial-gradient(ellipse 60% 50% at 50% 40%, rgba(13,110,115,0.15) 0%, transparent 70%)',
  subtle:
    'radial-gradient(ellipse 55% 45% at 50% 45%, rgba(13,110,115,0.12) 0%, transparent 70%)',
  cards:
    'radial-gradient(ellipse 60% 55% at 50% 55%, rgba(13,110,115,0.12) 0%, transparent 70%)',
  corner:
    'radial-gradient(circle at 30% 20%, rgba(13,110,115,0.1) 0%, transparent 40%)',
  chat:
    'radial-gradient(ellipse 70% 50% at 50% 40%, rgba(13,110,115,0.08) 0%, transparent 70%)',
  vignette:
    'radial-gradient(ellipse 100% 100% at 50% 50%, transparent 55%, rgba(15,28,29,0.5) 100%)',
}

function GradientBackdrop({ variant = 'default', gradient, className = '' }) {
  const bg = gradient || PRESETS[variant] || PRESETS.default

  return (
    <div
      className={`pointer-events-none absolute inset-0 ${className}`}
      aria-hidden
      style={{ background: bg }}
    />
  )
}

export default GradientBackdrop
