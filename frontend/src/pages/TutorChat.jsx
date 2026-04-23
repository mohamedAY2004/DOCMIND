import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
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

  return <TutorChatScreen subjectId={subjectId} subjectName={subjectName} />
}

export default TutorChat
