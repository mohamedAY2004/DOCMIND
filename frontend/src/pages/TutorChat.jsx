import { useEffect, useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { AlertTriangle } from 'lucide-react'
import TutorChatScreen from '../components/chat/TutorChatScreen'
import { getSubjectById } from '../services/subjectService'
import { titleCaseSlug } from '../utils/formatters'

function TutorChat() {
  const [searchParams] = useSearchParams()
  const subjectId = searchParams.get('subject') || ''
  const [subjectName, setSubjectName] = useState(() => titleCaseSlug(subjectId))

  useEffect(() => {
    if (!subjectId) return
    let cancelled = false
    getSubjectById(subjectId)
      .then((subject) => {
        if (!cancelled && subject?.title) setSubjectName(subject.title)
      })
      .catch(() => {
        /* keep slug-derived fallback */
      })
    return () => {
      cancelled = true
    }
  }, [subjectId])

  if (!subjectId) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-4 bg-dm-background px-6 text-center">
        <AlertTriangle size={40} className="text-amber-400" />
        <h1 className="text-xl font-semibold text-dm-foreground">No subject selected</h1>
        <p className="max-w-sm text-sm text-dm-muted">
          A subject is required to open the AI tutor. Please go back and select a subject from your list.
        </p>
        <Link
          to="/tutors"
          className="mt-2 rounded-xl bg-dm-primary px-5 py-2.5 text-sm font-semibold text-dm-foreground transition-colors hover:bg-dm-primary/80"
        >
          Back to tutors
        </Link>
      </div>
    )
  }

  return <TutorChatScreen subjectId={subjectId} subjectName={subjectName} />
}

export default TutorChat
