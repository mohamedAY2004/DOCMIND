import { useEffect, useState } from 'react'
import { Calendar } from 'lucide-react'
import {
  LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import { getDailyUsage } from '../../services/adminService'
import ChartCard from './ChartCard'
import ChartFilters from './ChartFilters'
import InlineSelect from './InlineSelect'
import { useSubjectFilters } from './useSubjectFilters'
import CustomTooltip from './CustomTooltip'
import { TIME_RANGES, unwrapList, useChartColors } from './chartUtils'

/**
 * Daily Usage Trends line chart. Time range plus semester / instructor /
 * subject are all sent to the backend so the series reflects the selection.
 */
function DailyUsageChart({ subjectStats, instructorsById, semesters }) {
  const chartColors = useChartColors()
  const filters = useSubjectFilters(subjectStats, instructorsById)
  const [timeRange, setTimeRange] = useState(14)
  const [data, setData] = useState([])

  const { semester, instructor, subject } = filters

  useEffect(() => {
    let cancelled = false
    getDailyUsage({
      days: Number(timeRange) || 14,
      semesterId: semester !== 'all' ? semester : undefined,
      instructorId: instructor !== 'all' ? instructor : undefined,
      subjectId: subject !== 'all' ? subject : undefined,
    })
      .then((res) => { if (!cancelled) setData(unwrapList(res)) })
      .catch(() => { if (!cancelled) setData([]) })
    return () => { cancelled = true }
  }, [timeRange, semester, instructor, subject])

  const headerFilters = (
    <>
      <InlineSelect
        icon={Calendar}
        ariaLabel="Time range"
        value={timeRange}
        onChange={(e) => setTimeRange(e.target.value)}
      >
        {TIME_RANGES.map((r) => (
          <option key={r.id} value={r.id}>{r.label}</option>
        ))}
      </InlineSelect>
      <ChartFilters filters={filters} semesters={semesters} showSubject />
    </>
  )

  return (
    <ChartCard
      title="Daily Usage Trends"
      filters={headerFilters}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3, duration: 0.4 }}
    >
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={data}>
          <CartesianGrid {...chartColors.grid} />
          <XAxis dataKey="day" tick={chartColors.axis} />
          <YAxis tick={chartColors.axis} allowDecimals={false} />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ fontSize: 12, color: chartColors.legendColor }} />
          <Line
            type="monotone"
            dataKey="conversations"
            name="Conversations"
            stroke="#0D6E73"
            strokeWidth={2}
            dot={{ r: 3, fill: '#0D6E73' }}
            activeDot={{ r: 5 }}
          />
          <Line
            type="monotone"
            dataKey="questions"
            name="Questions"
            stroke="#a78bfa"
            strokeWidth={2}
            dot={{ r: 3, fill: '#a78bfa' }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </ChartCard>
  )
}

export default DailyUsageChart
