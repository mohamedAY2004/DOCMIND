import { motion } from 'framer-motion'

const screenClass =
  'relative min-h-screen flex items-center justify-center bg-dm-background p-4 overflow-hidden'

const cardClass =
  'relative w-full max-w-md rounded-2xl border border-dm-border/50 bg-dm-card/80 backdrop-blur-xl p-8 shadow-2xl shadow-dm-primary/5 transition-shadow duration-300 hover:shadow-[0_25px_60px_-12px_rgb(var(--dm-primary)/0.15)]'

function AuthCard({ children, className = '' }) {
  return (
    <div className={screenClass}>
      <div
        className="pointer-events-none absolute inset-0"
        aria-hidden
        style={{
          background:
            'radial-gradient(ellipse 50% 45% at 50% 50%, rgb(var(--dm-primary) / 0.12) 0%, transparent 70%)',
        }}
      />
      <div
        className="pointer-events-none absolute inset-0"
        aria-hidden
        style={{
          background:
            'radial-gradient(ellipse 100% 100% at 50% 50%, transparent 50%, var(--dm-backdrop-vignette) 100%)',
        }}
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
