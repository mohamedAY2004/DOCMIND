import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Loader2 } from 'lucide-react'
import { AppLayout, AppTopBar } from '../components/layout'
import SubjectCard from '../components/ui/SubjectCard'
import GradientBackdrop from '../components/ui/GradientBackdrop'
import PageFooter from '../components/ui/PageFooter'
import { getStudentSubjects } from '../services/subjectService'
import docmindLogo from '../assets/docmind-logo.png'

import { stagger, fadeUp } from '../utils/motion'

function ChatWithTutors() {
  const [subjects, setSubjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    let cancelled = false
    getStudentSubjects()
      .then((data) => {
        if (cancelled) return
        setSubjects(Array.isArray(data) ? data : data?.items || [])
      })
      .catch(() => {
        if (!cancelled) setError(true)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <AppLayout
      scrollable
      topNav={
        <AppTopBar
          title="DocMind"
          logo={docmindLogo}
          logoClassName="h-14 w-auto object-contain"
          backTo="/home"
        />
      }
    >
      <div className="relative flex flex-1 flex-col">
        <GradientBackdrop variant="cards" />

        <div className="relative mx-auto w-full max-w-6xl flex-1 px-4 py-10 md:px-6 md:py-14">
          <motion.section
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <h1 className="text-4xl font-extrabold tracking-tight text-dm-foreground md:text-5xl">
              Chat with Tutors
            </h1>
            <p className="mt-3 text-base text-dm-muted/80 md:text-lg">
              Select a subject to start your AI-powered study session.
            </p>
          </motion.section>

          {loading ? (
            <div className="mt-16 flex items-center justify-center gap-3 text-dm-muted">
              <Loader2 size={20} className="animate-spin" />
              Loading subjects…
            </div>
          ) : error ? (
            <p className="mt-16 text-center text-dm-muted">
              Could not load subjects. Please try again.
            </p>
          ) : subjects.length === 0 ? (
            <p className="mt-16 text-center text-dm-muted">
              No subjects are available yet.
            </p>
          ) : (
            <motion.section
              className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3"
              variants={stagger()}
              initial="hidden"
              animate="visible"
            >
              {subjects.map((subject) => (
                <motion.div key={subject.id} variants={fadeUp}>
                  <SubjectCard
                    title={subject.title}
                    description={subject.description}
                    buttonText="Start Chatting →"
                    href={`/tutors/chat?subject=${subject.id}`}
                    className="h-full"
                  />
                </motion.div>
              ))}
            </motion.section>
          )}
        </div>

        <PageFooter />
      </div>
    </AppLayout>
  )
}

export default ChatWithTutors
