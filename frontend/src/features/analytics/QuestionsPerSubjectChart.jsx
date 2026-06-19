import { BookOpen } from 'lucide-react'
import {
  BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import ChartCard from './ChartCard'
import ChartFilters from './ChartFilters'
import ChartEmptyState from './ChartEmptyState'
import { useSubjectFilters } from './useSubjectFilters'
import CustomTooltip from './CustomTooltip'
import { subjectLabel, useChartColors } from './chartUtils'

/**
 * Tutor conversation count per subject. Filterable by semester / instructor.
 */
function QuestionsPerSubjectChart({ subjectStats, instructorsById, semesters }) {
  const chartColors = useChartColors()
  const filters = useSubjectFilters(subjectStats, instructorsById)

  const bars = filters.filtered.map((s) => ({
    name: subjectLabel(s.title),
    questions: s.interactions || 0,
  }))

  return (
    <ChartCard
      title="Questions per Subject"
      filters={<ChartFilters filters={filters} semesters={semesters} />}
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.45, duration: 0.4 }}
    >
      {bars.length > 0 ? (
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={bars}>
            <CartesianGrid {...chartColors.grid} />
            <XAxis dataKey="name" tick={chartColors.axis} interval={0} angle={-20} textAnchor="end" height={60} />
            <YAxis tick={chartColors.axis} allowDecimals={false} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="questions" name="Questions" fill="#0D6E73" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      ) : (
        <ChartEmptyState icon={BookOpen} message="No subjects match these filters." />
      )}
    </ChartCard>
  )
}

export default QuestionsPerSubjectChart
