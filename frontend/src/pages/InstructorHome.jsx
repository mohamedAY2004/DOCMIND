import { useEffect, useMemo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, LogOut, Loader2 } from 'lucide-react'
import { AppLayout, AppTopBar } from '../components/layout'
import InputField from '../components/ui/InputField'
import InstructorSubjectCard from '../components/ui/InstructorSubjectCard'
import GradientBackdrop from '../components/ui/GradientBackdrop'
import PageFooter from '../components/ui/PageFooter'
import useAuth from '../hooks/useAuth'
import {
  getInstructorSubjects,
  getSubjectInstructors,
} from '../services/subjectService'
import docmindLogo from '../assets/docmind-logo.png'
import { stagger, fadeUp } from '../utils/motion'
import { instructorDisplayName, normalizeInstructorRow } from '../utils/formatters'

function unwrapList(res) {
  if (!res) return []
  if (Array.isArray(res)) return res
  if (Array.isArray(res.items)) return res.items
  return []
}

function InstructorHome() {
  const { user, logout } = useAuth()
  const userId = user?.id ?? null
  const [search, setSearch] = useState('')
  const [subjects, setSubjects] = useState([])
  /** subjectId → normalized roster (preferred for ordering + display). */
  const [instructorsBySubjectId, setInstructorsBySubjectId] = useState({})
  /** Merged map from all roster responses (fallback if a subject slice is empty). */
  const [instructorsById, setInstructorsById] = useState({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!userId) return
    let cancelled = false
    setLoading(true)

    getInstructorSubjects(userId)
      .catch(() => [])
      .then(async (subjectsRes) => {
        if (cancelled) return
        const list = unwrapList(subjectsRes)
        setSubjects(list)

        // Resolve co-instructor display names via the per-subject roster
        // endpoint (accessible to anyone with subject access). Runs in
        // parallel; individual failures just leave that subject's roster
        // unresolved.
        const rosters = await Promise.all(
          list.map((s) =>
            getSubjectInstructors(s.id)
              .then(unwrapList)
              .catch(() => []),
          ),
        )
        if (cancelled) return
        const merged = {}
        const perSubject = {}
        list.forEach((s, idx) => {
          const rows = (rosters[idx] || [])
            .map(normalizeInstructorRow)
            .filter(Boolean)
          perSubject[s.id] = rows
          rows.forEach((r) => {
            merged[r.id] = r
          })
        })
        setInstructorsBySubjectId(perSubject)
        setInstructorsById(merged)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [userId])

  const resolveInstructors = (subject) => {
    const ids = (subject.instructorIds || []).map((id) => String(id).trim())
    const local = instructorsBySubjectId[subject.id] || []
    const byId = Object.fromEntries(local.map((r) => [r.id, r]))
    return ids.map((id) => {
      if (byId[id]) return byId[id]
      if (instructorsById[id]) return instructorsById[id]
      return { id, name: instructorDisplayName({ id }) }
    })
  }

  const instructorSubjects = useMemo(() => {
    if (!search.trim()) return subjects
    const q = search.toLowerCase()
    return subjects.filter((s) => {
      const roster = resolveInstructors(s)
      return (
        (s.title || '').toLowerCase().includes(q) ||
        (s.courseCode || '').toLowerCase().includes(q) ||
        (s.id || '').toLowerCase().includes(q) ||
        roster.some((i) => (i.name || '').toLowerCase().includes(q))
      )
    })
  }, [search, subjects, instructorsById, instructorsBySubjectId])

  return (
    <AppLayout
      scrollable
      topNav={
        <AppTopBar
          title="DocMind"
          logo={docmindLogo}
          logoClassName="h-14 w-auto object-contain"
          logoHref="/instructor"
        >
          <div className="ml-auto flex items-center gap-3">
            <div className="w-full max-w-[240px]">
              <InputField
                placeholder="Search Subjects"
                icon={<Search size={16} className="text-current" />}
                className="rounded-xl border-white/10 bg-white/5 backdrop-blur"
                compact
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <button
              type="button"
              onClick={logout}
              className="flex shrink-0 items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-dm-muted hover:bg-dm-background hover:text-dm-foreground transition-all duration-200"
              aria-label="Log out"
            >
              <LogOut size={18} className="shrink-0" />
              Log out
            </button>
          </div>
        </AppTopBar>
      }
    >
      <div className="relative flex flex-1 flex-col min-h-0">
        <GradientBackdrop variant="corner" />

        <div className="relative mx-auto max-w-6xl px-4 py-14 md:px-6 md:py-16">
          <motion.div
            className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <section>
              <h1 className="text-3xl font-bold text-dm-foreground md:text-4xl">My Subjects</h1>
              <p className="mt-2 text-dm-muted">
                Manage your course materials and AI assistants for the active
                semester. Subjects you co-teach show every instructor on the
                team.
              </p>
            </section>
            <button
              type="button"
              className="rounded-xl bg-dm-primary px-4 py-2.5 text-sm font-medium text-dm-foreground transition-all duration-200 hover:opacity-95 hover:scale-[1.03] active:scale-95"
            >
              Semester: Fall 2025
            </button>
          </motion.div>

          {loading ? (
            <div className="mt-16 flex items-center justify-center gap-3 text-dm-muted">
              <Loader2 size={20} className="animate-spin" />
              Loading subjects…
            </div>
          ) : (
            <motion.section
              className="mt-10 grid gap-8 sm:grid-cols-2 lg:grid-cols-3"
              variants={stagger(0.08)}
              initial="hidden"
              animate="visible"
            >
              <AnimatePresence mode="popLayout">
                {instructorSubjects.map((subject) => {
                  const roster = resolveInstructors(subject)
                  return (
                    <motion.div
                      key={subject.id}
                      variants={fadeUp}
                      layout
                      exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.2 } }}
                    >
                      <InstructorSubjectCard
                        title={subject.title}
                        courseCode={subject.courseCode}
                        pdfCount={subject.pdfCount}
                        status="ready"
                        href={`/instructor/subject/${subject.id}`}
                        className="h-full"
                        instructors={roster}
                        currentInstructorId={userId}
                      />
                    </motion.div>
                  )
                })}
              </AnimatePresence>
            </motion.section>
          )}

          {!loading && instructorSubjects.length === 0 && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mt-16 text-center text-dm-muted"
            >
              {search.trim()
                ? `No subjects match "${search}"`
                : 'You are not assigned to any subjects yet.'}
            </motion.p>
          )}
        </div>

        <PageFooter />
      </div>
    </AppLayout>
  )
}

export default InstructorHome
