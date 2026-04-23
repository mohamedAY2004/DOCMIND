export const stagger = (delay = 0.07) => ({
  hidden: {},
  visible: { transition: { staggerChildren: delay } },
})

export const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.35, ease: 'easeOut' } },
}

export const adminCardClass = 'rounded-2xl border border-dm-border bg-dm-card p-6 shadow-lg'
