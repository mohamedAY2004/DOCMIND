import { ThumbsUp } from 'lucide-react'
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
} from 'recharts'
import ChartCard from './ChartCard'
import ChartFilters from './ChartFilters'
import ChartEmptyState from './ChartEmptyState'
import { useSubjectFilters } from './useSubjectFilters'
import { PIE_COLORS } from './chartUtils'

/**
 * Positive vs negative feedback share across the selected subjects.
 * Filterable by semester / instructor / subject.
 */
function FeedbackDistributionChart({ subjectStats, instructorsById, semesters }) {
  const filters = useSubjectFilters(subjectStats, instructorsById)

  const positive = filters.filtered.reduce((acc, s) => acc + (s.thumbsUp || 0), 0)
  const negative = filters.filtered.reduce((acc, s) => acc + (s.thumbsDown || 0), 0)
  const hasFeedback = positive + negative > 0
  const pie = [
    { name: 'Positive', value: positive },
    { name: 'Negative', value: negative },
  ]

  return (
    <ChartCard
      title="Feedback Distribution"
      filters={<ChartFilters filters={filters} semesters={semesters} showSubject />}
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.45, duration: 0.4 }}
    >
      {hasFeedback ? (
        <>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pie}
                cx="50%"
                cy="50%"
                innerRadius={70}
                outerRadius={110}
                paddingAngle={4}
                dataKey="value"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {pie.map((_, i) => (
                  <Cell key={i} fill={PIE_COLORS[i]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-4 flex items-center justify-center gap-6">
            <span className="flex items-center gap-2 text-sm text-dm-muted">
              <span className="h-3 w-3 rounded-full bg-emerald-400" />
              Positive ({positive.toLocaleString()})
            </span>
            <span className="flex items-center gap-2 text-sm text-dm-muted">
              <span className="h-3 w-3 rounded-full bg-red-400" />
              Negative ({negative.toLocaleString()})
            </span>
          </div>
        </>
      ) : (
        <ChartEmptyState icon={ThumbsUp} message="No feedback data yet." />
      )}
    </ChartCard>
  )
}

export default FeedbackDistributionChart
