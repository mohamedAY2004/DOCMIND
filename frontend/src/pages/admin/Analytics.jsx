import { useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import {
  LineChart, Line,
  BarChart, Bar,
  PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import {
  Users, MessageSquare, BookOpen, ThumbsUp, Calendar, Filter, X,
} from 'lucide-react'
import AdminLayout from '../../components/layout/AdminLayout'
import MetricCard from '../../components/ui/MetricCard'
import {
  getUsers,
  getSubjectStats,
  getDailyUsage,
  getSemesters,
} from '../../services/adminService'
import { stagger, adminCardClass } from '../../utils/motion'

const CHART_AXIS = { fill: '#8AA3A5', fontSize: 12 }
const CHART_GRID = { strokeDasharray: '3 3', stroke: '#1F3A3B' }
const PIE_COLORS = ['#22c55e', '#ef4444']

const TIME_RANGES = [
  { id: 7, label: 'Last 7 days' },
  { id: 14, label: 'Last 14 days' },
  { id: 30, label: 'Last 30 days' },
  { id: 90, label: 'Last 90 days' },
]

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-xl border border-dm-border bg-dm-card px-4 py-3 shadow-xl">
      <p className="mb-1 text-xs font-medium text-dm-muted">{label}</p>
      {payload.map((p) => (
        <p key={p.dataKey} className="text-sm" style={{ color: p.color }}>
          {p.name}: <span className="font-semibold">{p.value.toLocaleString()}</span>
        </p>
      ))}
    </div>
  )
}

const selectClass = 'rounded-xl border border-dm-border bg-dm-card py-2 pl-3 pr-8 text-sm text-dm-foreground focus:outline-none focus:ring-2 focus:ring-dm-primary/40 appearance-none cursor-pointer'

function unwrapList(res) {
  if (!res) return []
  if (Array.isArray(res)) return res
  if (Array.isArray(res.items)) return res.items
  return []
}

function Analytics() {
  const [users, setUsers] = useState([])
  const [subjectStats, setSubjectStats] = useState([])
  const [dailyUsage, setDailyUsage] = useState([])
  const [semesters, setSemesters] = useState([])
  const [instructorsById, setInstructorsById] = useState({})

  const [timeRange, setTimeRange] = useState(14)
  const [semester, setSemester] = useState('all')
  const [subject, setSubject] = useState('all')
  const [instructor, setInstructor] = useState('all')

  useEffect(() => {
    let cancelled = false
    Promise.all([
      getUsers({ pageSize: 1000 }).catch(() => null),
      getSubjectStats().catch(() => []),
      getSemesters().catch(() => []),
      getUsers({ role: 'instructor', pageSize: 500 }).catch(() => null),
    ]).then(([usersRes, statsRes, semestersRes, instructorsRes]) => {
      if (cancelled) return
      setUsers(unwrapList(usersRes))
      setSubjectStats(unwrapList(statsRes))
      setSemesters(unwrapList(semestersRes))
      const map = {}
      unwrapList(instructorsRes)
        .filter((u) => u.role === 'instructor')
        .forEach((i) => { map[i.id] = i })
      setInstructorsById(map)
    })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    getDailyUsage(Number(timeRange) || 14)
      .then((res) => {
        if (cancelled) return
        setDailyUsage(unwrapList(res))
      })
      .catch(() => {
        if (!cancelled) setDailyUsage([])
      })
    return () => {
      cancelled = true
    }
  }, [timeRange])

  const instructors = useMemo(() => {
    const ids = new Set()
    subjectStats.forEach((s) => {
      (s.instructorIds || []).forEach((id) => ids.add(id))
    })
    return [...ids]
      .map((id) => instructorsById[id])
      .filter(Boolean)
  }, [subjectStats, instructorsById])

  const hasActiveFilters = semester !== 'all' || subject !== 'all' || instructor !== 'all' || Number(timeRange) !== 14

  const resetFilters = () => {
    setTimeRange(14)
    setSemester('all')
    setSubject('all')
    setInstructor('all')
  }

  const filteredSubjects = useMemo(() => {
    let list = subjectStats
    if (semester !== 'all') list = list.filter((s) => s.semester === semester)
    if (instructor !== 'all') {
      list = list.filter((s) => (s.instructorIds || []).includes(instructor))
    }
    if (subject !== 'all') list = list.filter((s) => s.id === subject)
    return list
  }, [subjectStats, semester, instructor, subject])

  const totalUsers = users.length
  const activeUsers = users.filter((u) => u.status === 'active').length
  const totalSubjects = filteredSubjects.length
  const totalConversations = filteredSubjects.reduce((s, x) => s + (x.interactions || 0), 0)
  const totalPositive = filteredSubjects.reduce((s, x) => s + (x.thumbsUp || 0), 0)
  const totalNegative = filteredSubjects.reduce((s, x) => s + (x.thumbsDown || 0), 0)
  const satisfactionPct = totalPositive + totalNegative > 0
    ? Math.round((totalPositive / (totalPositive + totalNegative)) * 100)
    : 0

  const overview = [
    { label: 'Total Users', value: totalUsers, icon: Users, accent: 'text-blue-400 bg-blue-400/10' },
    { label: 'Active Users', value: activeUsers, icon: Users, accent: 'text-emerald-400 bg-emerald-400/10' },
    { label: 'Subjects', value: totalSubjects, icon: BookOpen, accent: 'text-amber-400 bg-amber-400/10' },
    { label: 'AI Conversations', value: totalConversations.toLocaleString(), icon: MessageSquare, accent: 'text-purple-400 bg-purple-400/10' },
    { label: 'Positive Feedback', value: totalPositive.toLocaleString(), icon: ThumbsUp, accent: 'text-emerald-400 bg-emerald-400/10' },
    { label: 'Satisfaction', value: `${satisfactionPct}%`, icon: ThumbsUp, accent: 'text-dm-primary bg-dm-primary/10' },
  ]

  const feedbackPie = [
    { name: 'Positive', value: totalPositive || 1 },
    { name: 'Negative', value: totalNegative || 0 },
  ]

  const subjectBars = filteredSubjects.map((s) => ({
    name: (s.title || '').length > 12 ? s.title.slice(0, 12) + '…' : s.title,
    questions: s.interactions || 0,
    positive: s.thumbsUp || 0,
    negative: s.thumbsDown || 0,
  }))

  const subjectOptions = useMemo(() => {
    let list = subjectStats
    if (semester !== 'all') list = list.filter((s) => s.semester === semester)
    if (instructor !== 'all') {
      list = list.filter((s) => (s.instructorIds || []).includes(instructor))
    }
    return list
  }, [subjectStats, semester, instructor])

  return (
    <AdminLayout title="Analytics">
      <div className="mx-auto max-w-7xl px-6 py-8 flex flex-col gap-8">
        {/* Filters bar */}
        <motion.div
          className={`${adminCardClass} flex flex-col gap-4 sm:flex-row sm:items-center sm:flex-wrap`}
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <div className="flex items-center gap-2 text-dm-muted">
            <Filter size={16} />
            <span className="text-sm font-medium">Filters</span>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="flex flex-col gap-1">
              <label className="text-[11px] font-medium text-dm-muted uppercase tracking-wider">Time Range</label>
              <div className="relative">
                <Calendar size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-dm-muted" />
                <select
                  value={timeRange}
                  onChange={(e) => setTimeRange(e.target.value)}
                  className={`${selectClass} pl-9`}
                >
                  {TIME_RANGES.map((r) => (
                    <option key={r.id} value={r.id}>{r.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-[11px] font-medium text-dm-muted uppercase tracking-wider">Semester</label>
              <select
                value={semester}
                onChange={(e) => { setSemester(e.target.value); setSubject('all') }}
                className={selectClass}
              >
                <option value="all">All Semesters</option>
                {semesters.map((s) => (
                  <option key={s.id} value={s.id}>{s.label}</option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-[11px] font-medium text-dm-muted uppercase tracking-wider">Instructor</label>
              <select
                value={instructor}
                onChange={(e) => { setInstructor(e.target.value); setSubject('all') }}
                className={selectClass}
              >
                <option value="all">All Instructors</option>
                {instructors.map((i) => (
                  <option key={i.id} value={i.id}>{i.name}</option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-[11px] font-medium text-dm-muted uppercase tracking-wider">Subject</label>
              <select
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                className={selectClass}
              >
                <option value="all">All Subjects</option>
                {subjectOptions.map((s) => (
                  <option key={s.id} value={s.id}>{s.title}</option>
                ))}
              </select>
            </div>
          </div>

          {hasActiveFilters && (
            <button
              type="button"
              onClick={resetFilters}
              className="ml-auto flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium text-red-400 transition-colors hover:bg-red-400/10"
            >
              <X size={14} />
              Clear filters
            </button>
          )}
        </motion.div>

        {/* Overview metrics */}
        <motion.section
          className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
          variants={stagger()}
          initial="hidden"
          animate="visible"
        >
          {overview.map((m) => (
            <MetricCard key={m.label} icon={m.icon} value={m.value} label={m.label} accent={m.accent} />
          ))}
        </motion.section>

        {/* Usage trends — line chart */}
        <motion.section
          className={adminCardClass}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.4 }}
        >
          <h2 className="mb-6 text-lg font-semibold text-dm-foreground">Daily Usage Trends</h2>
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={dailyUsage}>
              <CartesianGrid {...CHART_GRID} />
              <XAxis dataKey="day" tick={CHART_AXIS} />
              <YAxis tick={CHART_AXIS} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 12, color: '#8AA3A5' }} />
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
        </motion.section>

        {subjectBars.length > 0 ? (
          <>
            <div className="grid gap-6 lg:grid-cols-2">
              {/* Questions per subject — bar chart */}
              <motion.section
                className={adminCardClass}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.45, duration: 0.4 }}
              >
                <h2 className="mb-6 text-lg font-semibold text-dm-foreground">Questions per Subject</h2>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={subjectBars}>
                    <CartesianGrid {...CHART_GRID} />
                    <XAxis dataKey="name" tick={CHART_AXIS} interval={0} angle={-20} textAnchor="end" height={60} />
                    <YAxis tick={CHART_AXIS} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="questions" name="Questions" fill="#0D6E73" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </motion.section>

              {/* Feedback distribution — pie chart */}
              <motion.section
                className={adminCardClass}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.45, duration: 0.4 }}
              >
                <h2 className="mb-6 text-lg font-semibold text-dm-foreground">Feedback Distribution</h2>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={feedbackPie}
                      cx="50%"
                      cy="50%"
                      innerRadius={70}
                      outerRadius={110}
                      paddingAngle={4}
                      dataKey="value"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {feedbackPie.map((_, i) => (
                        <Cell key={i} fill={PIE_COLORS[i]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
                <div className="mt-4 flex items-center justify-center gap-6">
                  <span className="flex items-center gap-2 text-sm text-dm-muted">
                    <span className="h-3 w-3 rounded-full bg-emerald-400" />
                    Positive ({totalPositive.toLocaleString()})
                  </span>
                  <span className="flex items-center gap-2 text-sm text-dm-muted">
                    <span className="h-3 w-3 rounded-full bg-red-400" />
                    Negative ({totalNegative.toLocaleString()})
                  </span>
                </div>
              </motion.section>
            </div>

            {/* Feedback per subject — stacked bar */}
            <motion.section
              className={adminCardClass}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6, duration: 0.4 }}
            >
              <h2 className="mb-6 text-lg font-semibold text-dm-foreground">Feedback Breakdown by Subject</h2>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={subjectBars}>
                  <CartesianGrid {...CHART_GRID} />
                  <XAxis dataKey="name" tick={CHART_AXIS} interval={0} angle={-20} textAnchor="end" height={60} />
                  <YAxis tick={CHART_AXIS} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{ fontSize: 12, color: '#8AA3A5' }} />
                  <Bar dataKey="positive" name="Positive" stackId="fb" fill="#22c55e" radius={[0, 0, 0, 0]} />
                  <Bar dataKey="negative" name="Negative" stackId="fb" fill="#ef4444" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </motion.section>
          </>
        ) : (
          <motion.div
            className={`${adminCardClass} flex flex-col items-center justify-center py-16`}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <BookOpen size={40} className="text-dm-muted/40 mb-3" />
            <p className="text-dm-muted text-sm">No subjects match the selected filters.</p>
            <button
              type="button"
              onClick={resetFilters}
              className="mt-3 text-sm font-medium text-dm-primary hover:underline"
            >
              Clear all filters
            </button>
          </motion.div>
        )}
      </div>
    </AdminLayout>
  )
}

export default Analytics
