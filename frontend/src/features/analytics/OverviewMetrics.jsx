import { motion } from 'framer-motion'
import { BookOpen, MessageSquare, ThumbsUp, Users } from 'lucide-react'
import MetricCard from '../../components/ui/MetricCard'
import { stagger } from '../../utils/motion'
import ChartFilters from './ChartFilters'
import { useSubjectFilters } from './useSubjectFilters'

/**
 * Top-of-page summary cards. User totals are global; subject-derived metrics
 * (subjects, conversations, feedback, satisfaction) respond to this section's
 * own semester / instructor filter.
 */
function OverviewMetrics({ users, subjectStats, instructorsById, semesters }) {
  const filters = useSubjectFilters(subjectStats, instructorsById)

  const totalUsers = users.length
  const activeUsers = users.filter((u) => u.status === 'active').length
  const totalSubjects = filters.filtered.length
  const totalConversations = filters.filtered.reduce((s, x) => s + (x.interactions || 0), 0)
  const totalPositive = filters.filtered.reduce((s, x) => s + (x.thumbsUp || 0), 0)
  const totalNegative = filters.filtered.reduce((s, x) => s + (x.thumbsDown || 0), 0)
  const satisfactionPct = totalPositive + totalNegative > 0
    ? Math.round((totalPositive / (totalPositive + totalNegative)) * 100)
    : 0

  const cards = [
    { label: 'Total Users', value: totalUsers, icon: Users, accent: 'text-blue-400 bg-blue-400/10' },
    { label: 'Active Users', value: activeUsers, icon: Users, accent: 'text-emerald-400 bg-emerald-400/10' },
    { label: 'Subjects', value: totalSubjects, icon: BookOpen, accent: 'text-amber-400 bg-amber-400/10' },
    { label: 'AI Conversations', value: totalConversations.toLocaleString(), icon: MessageSquare, accent: 'text-purple-400 bg-purple-400/10' },
    { label: 'Positive Feedback', value: totalPositive.toLocaleString(), icon: ThumbsUp, accent: 'text-emerald-400 bg-emerald-400/10' },
    { label: 'Satisfaction', value: `${satisfactionPct}%`, icon: ThumbsUp, accent: 'text-dm-primary bg-dm-primary/10' },
  ]

  return (
    <section className="flex flex-col gap-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-lg font-semibold text-dm-foreground">Overview</h2>
        <div className="flex flex-wrap items-center gap-2">
          <ChartFilters filters={filters} semesters={semesters} />
        </div>
      </div>
      <motion.div
        className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
        variants={stagger()}
        initial="hidden"
        animate="visible"
      >
        {cards.map((m) => (
          <MetricCard key={m.label} icon={m.icon} value={m.value} label={m.label} accent={m.accent} />
        ))}
      </motion.div>
    </section>
  )
}

export default OverviewMetrics
