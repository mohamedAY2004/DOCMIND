import { useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { Search, LogOut, Loader2 } from 'lucide-react'
import { AppLayout, AppTopBar } from '../components/layout'
import InputField from '../components/ui/InputField'
import InstructorSubjectCard from '../components/ui/InstructorSubjectCard'
import CollapsibleSubjectSection from '../components/ui/CollapsibleSubjectSection'
import GradientBackdrop from '../components/ui/GradientBackdrop'
import PageFooter from '../components/ui/PageFooter'
import ThemeToggle from '../components/ui/ThemeToggle'
import useAuth from '../hooks/useAuth'
import { getInstructorSubjects, getSemesters } from '../services/subjectService'
import { groupSubjectsBySemester } from '../utils/groupSubjectsBySemester'
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
  const [semesters, setSemesters] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!userId) return
    let cancelled = false
    setLoading(true)

    // Semesters fail soft → grouping degrades to per-semesterId sections.
    Promise.all([
      getInstructorSubjects(userId).catch(() => []),
      getSemesters().catch(() => []),
    ])
      .then(([subjectsRes, semestersRes]) => {
        if (cancelled) return
        setSubjects(unwrapList(subjectsRes))
        setSemesters(unwrapList(semestersRes))
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

  // Search narrows first, then the filtered subjects are split into sections.
  const groups = useMemo(
    () => groupSubjectsBySemester(instructorSubjects, semesters),
    [instructorSubjects, semesters],
  )
  const hasActive = groups.some((g) => g.semester?.state === 'active')

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
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <h1 className="text-3xl font-bold text-dm-foreground md:text-4xl">My Subjects</h1>
            <p className="mt-2 text-dm-muted">
              View and manage your assigned subjects, grouped by semester.
            </p>
          </motion.div>

          {loading ? (
            <div className="mt-16 flex items-center justify-center gap-3 text-dm-muted">
              <Loader2 size={20} className="animate-spin" />
              Loading subjects…
            </div>
          ) : (
            groups.map((group, idx) => {
              const sem = group.semester
              return (
                <CollapsibleSubjectSection
                  key={sem?.id ?? '__other__'}
                  title={sem?.label ?? 'Other'}
                  state={sem?.state}
                  count={group.subjects.length}
                  defaultOpen={hasActive ? sem?.state === 'active' : idx === 0}
                >
                  <motion.div
                    className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3"
                    variants={stagger(0.08)}
                    initial="hidden"
                    animate="visible"
                  >
                    {group.subjects.map((subject) => {
                      const instructorRole =
                        subject.superInstructorId === userId ? 'super' : 'viewer'
                      const archived =
                        sem?.state === 'archived' ||
                        subject.semesterState === 'archived'
                      return (
                        <motion.div key={subject.id} variants={fadeUp}>
                          <InstructorSubjectCard
                            title={subject.title}
                            courseCode={subject.courseCode}
                            pdfCount={subject.pdfCount}
                            status={archived ? 'archived' : 'ready'}
                            href={`/instructor/subject/${subject.id}`}
                            className="h-full"
                            instructorRole={instructorRole}
                            isArchived={archived}
                          />
                        </motion.div>
                      )
                    })}
                  </motion.div>
                </CollapsibleSubjectSection>
              )
            })
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
