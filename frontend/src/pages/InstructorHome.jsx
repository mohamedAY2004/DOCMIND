import { useEffect, useMemo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, LogOut, Loader2 } from 'lucide-react'
import { AppLayout, AppTopBar } from '../components/layout'
import InputField from '../components/ui/InputField'
import InstructorSubjectCard from '../components/ui/InstructorSubjectCard'
import GradientBackdrop from '../components/ui/GradientBackdrop'
import PageFooter from '../components/ui/PageFooter'
import ThemeToggle from '../components/ui/ThemeToggle'
import useAuth from '../hooks/useAuth'
import { getInstructorSubjects } from '../services/subjectService'
import { primarySurfaceClass } from '../constants/themeClasses'
import { stagger, fadeUp } from '../utils/motion'

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
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!userId) return
    let cancelled = false
    setLoading(true)

    getInstructorSubjects(userId)
      .catch(() => [])
      .then((subjectsRes) => {
        if (cancelled) return
        setSubjects(unwrapList(subjectsRes))
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [userId])

  const instructorSubjects = useMemo(() => {
    if (!search.trim()) return subjects
    const q = search.toLowerCase()
    return subjects.filter(
      (s) =>
        (s.title || '').toLowerCase().includes(q) ||
        (s.courseCode || '').toLowerCase().includes(q) ||
        (s.id || '').toLowerCase().includes(q),
    )
  }, [search, subjects])

  return (
    <AppLayout
      scrollable
      topNav={
        <AppTopBar
          title="DocMind"
          showLogo
          logoClassName="h-14 w-auto object-contain"
          logoHref="/instructor"
        >
          <div className="ml-auto flex items-center gap-3">
            <div className="w-full max-w-[240px]">
              <InputField
                placeholder="Search Subjects"
                icon={<Search size={16} className="text-current" />}
                className="rounded-xl border-dm-border/50 bg-dm-background/50 backdrop-blur"
                compact
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <ThemeToggle />
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
                View and manage your assigned subjects for the active semester.
              </p>
            </section>
            <button
              type="button"
              className={`${primarySurfaceClass} rounded-xl px-4 py-2.5 text-sm font-medium transition-all duration-200 hover:opacity-95 hover:scale-[1.03] active:scale-95`}
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
                  const instructorRole =
                    subject.superInstructorId === userId ? 'super' : 'viewer'
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
                        instructorRole={instructorRole}
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
