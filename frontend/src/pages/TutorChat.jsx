import { useEffect, useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { AlertTriangle } from 'lucide-react'
import TutorChatScreen from '../components/chat/TutorChatScreen'
import { getSubjectById } from '../services/subjectService'
import { titleCaseSlug } from '../utils/formatters'
import { primarySurfaceClass } from '../constants/themeClasses'

function TutorChat() {
  const [searchParams] = useSearchParams()
  const subjectId = searchParams.get('subject') || ''
  const [subjectName, setSubjectName] = useState(() => titleCaseSlug(subjectId))
  const [semesterState, setSemesterState] = useState('active')

  useEffect(() => {
    if (!subjectId) return
    let cancelled = false
    getSubjectById(subjectId)
      .then((subject) => {
        if (cancelled) return
        if (subject?.title) setSubjectName(subject.title)
        if (subject?.semesterState) setSemesterState(subject.semesterState)
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
          className={`${primarySurfaceClass} mt-2 rounded-xl px-5 py-2.5 text-sm font-semibold transition-colors hover:opacity-95`}
        >
          Back to tutors
        </Link>
      </div>
    )
  }

  return (
    <TutorChatScreen
      subjectId={subjectId}
      subjectName={subjectName}
      semesterState={semesterState}
    />
  )
}

export default TutorChat
