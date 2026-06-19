import { motion } from 'framer-motion'
import { adminCardClass } from '../../utils/motion'

/**
 * Chart container with a header that holds the title and an optional slot for
 * per-diagram filter controls. Extra motion props are forwarded to the section.
 */
function ChartCard({ title, filters, children, className = '', ...motionProps }) {
  return (
    <motion.section className={`${adminCardClass} ${className}`} {...motionProps}>
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <h2 className="text-lg font-semibold text-dm-foreground">{title}</h2>
        {filters ? (
          <div className="flex flex-wrap items-center gap-2">{filters}</div>
        ) : null}
      </div>
      {children}
    </motion.section>
  )
}

export default ChartCard
