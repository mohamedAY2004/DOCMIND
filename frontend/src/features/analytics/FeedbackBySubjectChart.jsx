import { ThumbsUp } from 'lucide-react'
import {
  BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import ChartCard from './ChartCard'
import ChartFilters from './ChartFilters'
import ChartEmptyState from './ChartEmptyState'
import { useSubjectFilters } from './useSubjectFilters'
import CustomTooltip from './CustomTooltip'
import { subjectLabel, useChartColors } from './chartUtils'

/**
 * Positive / negative feedback stacked per subject.
 * Filterable by semester / instructor.
 */
function FeedbackBySubjectChart({ subjectStats, instructorsById, semesters }) {
  const chartColors = useChartColors()
  const filters = useSubjectFilters(subjectStats, instructorsById)

  const bars = filters.filtered
    .map((s) => ({
      name: subjectLabel(s.title),
      positive: s.thumbsUp || 0,
      negative: s.thumbsDown || 0,
    }))
    .filter((b) => b.positive + b.negative > 0)

  return (
    <ChartCard
      title="Feedback Breakdown by Subject"
      filters={<ChartFilters filters={filters} semesters={semesters} />}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.6, duration: 0.4 }}
    >
      {bars.length > 0 ? (
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={bars}>
            <CartesianGrid {...chartColors.grid} />
            <XAxis dataKey="name" tick={chartColors.axis} interval={0} angle={-20} textAnchor="end" height={60} />
            <YAxis tick={chartColors.axis} allowDecimals={false} />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: 12, color: chartColors.legendColor }} />
            <Bar dataKey="positive" name="Positive" stackId="fb" fill="#22c55e" radius={[0, 0, 0, 0]} />
            <Bar dataKey="negative" name="Negative" stackId="fb" fill="#ef4444" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      ) : (
        <ChartEmptyState icon={ThumbsUp} message="No feedback data for these filters." heightClass="h-[320px]" />
      )}
    </ChartCard>
  )
}

export default FeedbackBySubjectChart
