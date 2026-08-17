import { motion } from 'framer-motion'

const screenClass =
  'relative min-h-screen flex items-center justify-center bg-dm-background p-4 overflow-hidden'

const cardClass =
  'relative w-full max-w-md rounded-2xl border border-dm-border/50 bg-dm-card/80 backdrop-blur-xl p-8 shadow-2xl shadow-dm-primary/5 transition-shadow duration-300 hover:shadow-[0_25px_60px_-12px_rgb(var(--dm-primary)/0.15)]'

function AuthCard({ children, className = '' }) {
  return (
    <div className={screenClass}>
      <div
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_50%_45%_at_50%_50%,rgb(var(--dm-primary)/0.12)_0%,transparent_70%)]"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_100%_100%_at_50%_50%,transparent_50%,var(--dm-backdrop-vignette)_100%)]"
        aria-hidden
      />
      <motion.div
        className={[cardClass, className].filter(Boolean).join(' ')}
        initial={{ opacity: 0, y: 30, scale: 0.96 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      >
        {children}
      </motion.div>
    </div>
  )
}

export default AuthCard
