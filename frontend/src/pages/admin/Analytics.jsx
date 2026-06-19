import { useEffect, useState } from 'react'
import AdminLayout from '../../components/layout/AdminLayout'
import {
  getUsers,
  getSubjectStats,
  getSemesters,
} from '../../services/adminService'
import { unwrapList } from '../../features/analytics/chartUtils'
import OverviewMetrics from '../../features/analytics/OverviewMetrics'
import DailyUsageChart from '../../features/analytics/DailyUsageChart'
import QuestionsPerSubjectChart from '../../features/analytics/QuestionsPerSubjectChart'
import FeedbackDistributionChart from '../../features/analytics/FeedbackDistributionChart'
import FeedbackBySubjectChart from '../../features/analytics/FeedbackBySubjectChart'

function Analytics() {
  const [users, setUsers] = useState([])
  const [subjectStats, setSubjectStats] = useState([])
  const [semesters, setSemesters] = useState([])
  const [instructorsById, setInstructorsById] = useState({})

  useEffect(() => {
    let cancelled = false
    Promise.all([
      getUsers({ pageSize: 1000 }).catch(() => null),
      getSubjectStats({ pageSize: 1000 }).catch(() => []),
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

  const shared = { subjectStats, instructorsById, semesters }

  return (
    <AdminLayout title="Analytics">
      <div className="mx-auto flex max-w-7xl flex-col gap-8 px-6 py-8">
        <OverviewMetrics users={users} {...shared} />

        <DailyUsageChart {...shared} />

        <div className="grid gap-6 lg:grid-cols-2">
          <QuestionsPerSubjectChart {...shared} />
          <FeedbackDistributionChart {...shared} />
        </div>

        <FeedbackBySubjectChart {...shared} />
      </div>
    </AdminLayout>
  )
}

export default Analytics
