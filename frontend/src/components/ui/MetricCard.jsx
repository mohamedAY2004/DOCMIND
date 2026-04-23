import { motion } from 'framer-motion'
import { fadeUp } from '../../utils/motion'

function MetricCard({ icon: Icon, value, label, accent }) {
  return (
    <motion.div
      variants={fadeUp}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
      className="flex items-center gap-4 rounded-2xl border border-dm-border bg-dm-card p-5 shadow-lg transition-colors duration-200 hover:border-dm-primary/30"
    >
      <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl ${accent}`}>
        <Icon size={22} />
      </div>
      <div>
        <p className="text-2xl font-bold text-dm-foreground">{value}</p>
        <p className="text-sm text-dm-muted">{label}</p>
      </div>
    </motion.div>
  )
}

export default MetricCard
