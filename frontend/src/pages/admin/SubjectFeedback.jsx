import { useState, useMemo, useCallback, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
import {
  Search,
  ThumbsUp,
  ThumbsDown,
  MessageSquare,
  Bot,
  ChevronDown,
  ChevronUp,
  Filter,
  FileDown,
  Loader2,
} from 'lucide-react'
import AdminLayout from '../../components/layout/AdminLayout'
import { primaryButtonCompactClass, primaryChipActiveClass } from '../../constants/themeClasses'
import {
  getSubjectStats,
  getFeedback,
  getSemesters,
  getUsers,
} from '../../services/adminService'
import { generateFeedbackReport } from '../../utils/generateFeedbackReport'
import { stagger, fadeUp, adminCardClass } from '../../utils/motion'

function unwrapList(res) {
  if (!res) return []
  if (Array.isArray(res)) return res
  if (Array.isArray(res.items)) return res.items
  return []
}

const selectClass =
  'rounded-xl border border-dm-border bg-dm-card py-2.5 pl-3 pr-8 text-sm text-dm-foreground focus:outline-none focus:ring-2 focus:ring-dm-primary/40 appearance-none cursor-pointer'

function SatisfactionBar({ up, down }) {
  const total = up + down
  const pct = total ? Math.round((up / total) * 100) : 0
  return (
    <div className="flex items-center gap-3">
      <div className="h-2 flex-1 rounded-full bg-dm-border overflow-hidden">
        <motion.div
          className="h-full rounded-full bg-emerald-400"
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.7, ease: 'easeOut', delay: 0.2 }}
        />
      </div>
      <span className="shrink-0 text-sm font-medium text-dm-foreground tabular-nums">
        {pct}%
      </span>
    </div>
  )
}

function SubjectFeedback() {
  const [subjects, setSubjects] = useState([])
  const [feedback, setFeedback] = useState([])
  const [semesters, setSemesters] = useState([])
  const [instructorsById, setInstructorsById] = useState({})

  const [subjectSearch, setSubjectSearch] = useState('')
  const [semester, setSemester] = useState('all')
  const [expandedSubjectId, setExpandedSubjectId] = useState(null)
  const [feedbackFilter, setFeedbackFilter] = useState('all')
  const [isGenerating, setIsGenerating] = useState(false)

  useEffect(() => {
    let cancelled = false
    Promise.all([
      getSubjectStats({ pageSize: 1000 }).catch(() => []),
      getFeedback({ pageSize: 1000 }).catch(() => []),
      getSemesters().catch(() => []),
      getUsers({ role: 'instructor', pageSize: 500 }).catch(() => null),
    ])
      .then(([statsRes, feedbackRes, semestersRes, usersRes]) => {
        if (cancelled) return
        setSubjects(unwrapList(statsRes))
        setFeedback(unwrapList(feedbackRes))
        setSemesters(unwrapList(semestersRes))
        const instructors = unwrapList(usersRes).filter(
          (u) => u.role === 'instructor',
        )
        const map = {}
        instructors.forEach((i) => {
          map[i.id] = i
        })
        setInstructorsById(map)
      })
      .catch(() => {
        if (!cancelled) toast.error('Could not load subject data.')
      })
    return () => {
      cancelled = true
    }
  }, [])

  const resolveInstructors = useCallback(
    (subject) => {
      const ids = subject.instructorIds || []
      return ids.map((id) => instructorsById[id]).filter(Boolean)
    },
    [instructorsById],
  )

  const filteredSubjects = useMemo(() => {
    let list = subjects
    if (semester !== 'all') {
      list = list.filter((s) => s.semester === semester)
    }
    if (subjectSearch.trim()) {
      const q = subjectSearch.toLowerCase()
      list = list.filter((s) => {
        const rosterNames = resolveInstructors(s).map((i) =>
          i.name.toLowerCase(),
        )
        return (
          (s.title || '').toLowerCase().includes(q) ||
          rosterNames.some((n) => n.includes(q))
        )
      })
    }
    return list
  }, [subjects, subjectSearch, semester, resolveInstructors])

  const expandedSubject = useMemo(
    () => subjects.find((s) => s.id === expandedSubjectId) || null,
    [subjects, expandedSubjectId],
  )

  const filteredFeedback = useMemo(() => {
    let result = feedback
    if (semester !== 'all') {
      result = result.filter((f) => f.semester === semester)
    }
    if (expandedSubjectId) {
      result = result.filter((f) => f.subjectId === expandedSubjectId)
    }
    if (feedbackFilter !== 'all') {
      result = result.filter((f) => f.feedback === feedbackFilter)
    }
    return result
  }, [feedback, expandedSubjectId, feedbackFilter, semester])

  const toggleSubject = (id) => {
    setExpandedSubjectId((prev) => (prev === id ? null : id))
    setFeedbackFilter('all')
  }

  const handleGenerateReport = useCallback(async () => {
    setIsGenerating(true)
    const semesterLabel =
      semester !== 'all'
        ? semesters.find((s) => s.id === semester)?.label
        : null

    try {
      await generateFeedbackReport(filteredFeedback, filteredSubjects, {
        semester: semesterLabel,
        subject: expandedSubject?.title,
        sentiment: feedbackFilter,
      })
    } finally {
      setIsGenerating(false)
    }
  }, [
    filteredFeedback,
    filteredSubjects,
    semester,
    expandedSubject,
    feedbackFilter,
    semesters,
  ])

  const activeSemesterLabel =
    semester !== 'all'
      ? semesters.find((s) => s.id === semester)?.label
      : null

  return (
    <AdminLayout title="Feedback & Insights">
      <div className="mx-auto max-w-7xl px-6 py-8 flex flex-col gap-6">
        {/* Toolbar: search + semester filter */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div className="flex flex-wrap items-end gap-3">
            <div className="flex flex-col gap-1">
              <label className="text-[11px] font-medium text-dm-muted uppercase tracking-wider">
                Search
              </label>
              <div className="relative w-full max-w-xs">
                <Search
                  size={16}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-dm-muted"
                />
                <input
                  type="text"
                  placeholder="Search subjects or instructors…"
                  value={subjectSearch}
                  onChange={(e) => setSubjectSearch(e.target.value)}
                  className="w-full rounded-xl border border-dm-border bg-dm-card py-2.5 pl-10 pr-4 text-sm text-dm-foreground placeholder:text-dm-muted focus:outline-none focus:ring-2 focus:ring-dm-primary/40"
                />
              </div>
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-[11px] font-medium text-dm-muted uppercase tracking-wider">
                Semester
              </label>
              <select
                value={semester}
                onChange={(e) => {
                  setSemester(e.target.value)
                  setExpandedSubjectId(null)
                }}
                className={selectClass}
              >
                <option value="all">All Semesters</option>
                {semesters.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {activeSemesterLabel && (
            <span className="rounded-full bg-dm-primary/10 px-3 py-1 text-xs font-medium text-dm-primary">
              Showing: {activeSemesterLabel}
            </span>
          )}
        </div>

        {/* Subject cards */}
        <motion.div
          className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
          variants={stagger(0.06)}
          initial="hidden"
          animate="visible"
        >
          <AnimatePresence mode="popLayout">
            {filteredSubjects.map((s) => {
              const total = s.thumbsUp + s.thumbsDown
              const pct = total ? Math.round((s.thumbsUp / total) * 100) : 0
              const isExpanded = expandedSubjectId === s.id
              const semLabel = semesters.find((sem) => sem.id === s.semester)
                ?.label
              const instructors = resolveInstructors(s)

              return (
                <motion.button
                  key={s.id}
                  variants={fadeUp}
                  layout
                  exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.2 } }}
                  whileHover={{ y: -3, transition: { duration: 0.15 } }}
                  type="button"
                  onClick={() => toggleSubject(s.id)}
                  className={`${adminCardClass} text-left transition-all duration-200 hover:shadow-xl ${
                    isExpanded
                      ? 'ring-2 ring-dm-primary/40 border-dm-primary/40'
                      : 'hover:border-dm-primary/30'
                  }`}
                >
                  <div className="flex items-start justify-between mb-3 gap-3">
                    <div className="min-w-0">
                      <h3 className="font-semibold text-dm-foreground">
                        {s.title}
                      </h3>
                      {semLabel && (
                        <span className="mt-1 inline-block rounded-full bg-dm-primary/10 px-2 py-0.5 text-[10px] font-medium text-dm-primary">
                          {semLabel}
                        </span>
                      )}
                    </div>
                    <div className="flex shrink-0 items-center gap-2">
                      {isExpanded ? (
                        <ChevronUp size={18} className="text-dm-primary" />
                      ) : (
                        <ChevronDown size={18} className="text-dm-muted" />
                      )}
                    </div>
                  </div>

                  {instructors.length > 0 && (
                    <div className="mb-3 flex flex-wrap items-center gap-1.5">
                      <span className="text-[10px] font-medium uppercase tracking-wider text-dm-muted">
                        Instructors
                      </span>
                      {instructors.map((i) => {
                        const isSuper = i.id === s.superInstructorId
                        return (
                          <span
                            key={i.id}
                            className={[
                              'rounded-full border px-2 py-0.5 text-[11px]',
                              isSuper
                                ? 'border-dm-primary/40 bg-dm-primary/10 text-dm-primary'
                                : 'border-dm-border bg-dm-background text-dm-muted',
                            ].join(' ')}
                          >
                            {i.name}
                            {isSuper && (
                              <span className="ml-1 font-medium">★</span>
                            )}
                          </span>
                        )
                      })}
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-3 mb-4">
                    <div className="flex items-center gap-2">
                      <MessageSquare size={14} className="text-purple-400" />
                      <span className="text-sm text-dm-muted">
                        <span className="font-medium text-dm-foreground">
                          {(s.interactions || 0).toLocaleString()}
                        </span>{' '}
                        chats
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Bot size={14} className="text-blue-400" />
                      <span className="text-sm text-dm-muted">
                        <span className="font-medium text-dm-foreground">
                          {(s.aiResponses || 0).toLocaleString()}
                        </span>{' '}
                        responses
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <ThumbsUp size={14} className="text-emerald-400" />
                      <span className="text-sm text-dm-foreground font-medium">
                        {(s.thumbsUp || 0).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <ThumbsDown size={14} className="text-red-400" />
                      <span className="text-sm text-dm-foreground font-medium">
                        {s.thumbsDown || 0}
                      </span>
                    </div>
                  </div>

                  <SatisfactionBar
                    up={s.thumbsUp || 0}
                    down={s.thumbsDown || 0}
                  />
                  <p className="text-xs text-dm-muted mt-2">
                    {pct}% satisfaction rate
                  </p>
                </motion.button>
              )
            })}
          </AnimatePresence>
        </motion.div>

        {filteredSubjects.length === 0 && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="py-8 text-center text-dm-muted"
          >
            No subjects match your filters.
          </motion.p>
        )}

        {/* Feedback panel */}
        <motion.section
          className={adminCardClass}
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.4 }}
        >
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-5">
            <h2 className="text-lg font-semibold text-dm-foreground">
              {expandedSubject
                ? `Feedback — ${expandedSubject.title}`
                : 'All Feedback'}
            </h2>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1">
                <Filter size={14} className="text-dm-muted" />
                {['all', 'up', 'down'].map((f) => (
                  <button
                    key={f}
                    type="button"
                    onClick={() => setFeedbackFilter(f)}
                    className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-all duration-200 ${
                      feedbackFilter === f
                        ? primaryChipActiveClass
                        : 'text-dm-muted hover:bg-dm-background hover:text-dm-foreground'
                    }`}
                  >
                    {f === 'all' ? 'All' : f === 'up' ? 'Positive' : 'Negative'}
                  </button>
                ))}
              </div>

              <button
                type="button"
                onClick={handleGenerateReport}
                disabled={isGenerating || filteredFeedback.length === 0}
                className={`${primaryButtonCompactClass} px-4 py-2 text-xs disabled:cursor-not-allowed disabled:opacity-40`}
              >
                {isGenerating ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  <FileDown size={14} />
                )}
                {isGenerating ? 'Generating…' : 'Download Report'}
              </button>
            </div>
          </div>

          <div className="flex flex-col gap-3 max-h-[520px] overflow-y-auto">
            <AnimatePresence mode="popLayout">
              {filteredFeedback.length === 0 && (
                <motion.p
                  key="empty"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="py-8 text-center text-dm-muted"
                >
                  No feedback entries found.
                </motion.p>
              )}
              {filteredFeedback.map((f) => (
                <motion.div
                  key={f.id}
                  layout
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.25 }}
                  className="rounded-xl border border-dm-border/50 bg-dm-background/50 p-4 transition-colors hover:border-dm-border"
                >
                  <div className="flex items-start justify-between gap-4 mb-3">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-dm-foreground">
                        {f.student}
                      </p>
                      <p className="text-xs text-dm-muted">
                        {f.subject} · {f.timestamp}
                      </p>
                    </div>
                    <span
                      className={`shrink-0 flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${
                        f.feedback === 'up'
                          ? 'bg-emerald-400/10 text-emerald-400'
                          : 'bg-red-400/10 text-red-400'
                      }`}
                    >
                      {f.feedback === 'up' ? (
                        <ThumbsUp size={12} />
                      ) : (
                        <ThumbsDown size={12} />
                      )}
                      {f.feedback === 'up' ? 'Positive' : 'Negative'}
                    </span>
                  </div>
                  <div className="mb-2">
                    <p className="text-xs font-medium text-dm-muted mb-1">
                      Question
                    </p>
                    <p className="text-sm text-dm-foreground">{f.question}</p>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-dm-muted mb-1">
                      AI Response
                    </p>
                    <p className="text-sm text-dm-foreground/80 line-clamp-3">
                      {f.aiResponse}
                    </p>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </motion.section>
      </div>
    </AdminLayout>
  )
}

export default SubjectFeedback
