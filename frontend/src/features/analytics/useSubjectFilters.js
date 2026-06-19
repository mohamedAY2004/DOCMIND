import { useMemo, useState } from 'react'

/**
 * Local, per-diagram filter state over the all-time `subjectStats` payload.
 *
 * Each chart instantiates its own copy so filters are independent across
 * diagrams. Returns the current selections, the option lists (cascaded so the
 * subject list respects the chosen semester/instructor) and the filtered
 * subject rows the chart should render.
 */
export function useSubjectFilters(subjectStats, instructorsById) {
  const [semester, setSemester] = useState('all')
  const [instructor, setInstructor] = useState('all')
  const [subject, setSubject] = useState('all')

  const instructorOptions = useMemo(() => {
    const ids = new Set()
    subjectStats.forEach((s) => (s.instructorIds || []).forEach((id) => ids.add(id)))
    return [...ids].map((id) => instructorsById[id]).filter(Boolean)
  }, [subjectStats, instructorsById])

  const subjectOptions = useMemo(() => {
    let list = subjectStats
    if (semester !== 'all') list = list.filter((s) => s.semester === semester)
    if (instructor !== 'all') {
      list = list.filter((s) => (s.instructorIds || []).includes(instructor))
    }
    return list
  }, [subjectStats, semester, instructor])

  const filtered = useMemo(() => {
    let list = subjectStats
    if (semester !== 'all') list = list.filter((s) => s.semester === semester)
    if (instructor !== 'all') {
      list = list.filter((s) => (s.instructorIds || []).includes(instructor))
    }
    if (subject !== 'all') list = list.filter((s) => s.id === subject)
    return list
  }, [subjectStats, semester, instructor, subject])

  const changeSemester = (value) => {
    setSemester(value)
    setSubject('all')
  }
  const changeInstructor = (value) => {
    setInstructor(value)
    setSubject('all')
  }
  const reset = () => {
    setSemester('all')
    setInstructor('all')
    setSubject('all')
  }

  return {
    semester,
    instructor,
    subject,
    setSemester: changeSemester,
    setInstructor: changeInstructor,
    setSubject,
    instructorOptions,
    subjectOptions,
    filtered,
    reset,
    isActive: semester !== 'all' || instructor !== 'all' || subject !== 'all',
  }
}
