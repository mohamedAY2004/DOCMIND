import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Users,
  BookOpen,
  BarChart3,
  MessageSquare,
  Activity,
  ArrowRight,
  ThumbsUp,
  Clock,
} from 'lucide-react'
import AdminLayout from '../../components/layout/AdminLayout'
import MetricCard from '../../components/ui/MetricCard'
import { stagger, adminCardClass } from '../../utils/motion'
import {
  getUsers,
  getSubjectStats,
  getActivityLog,
} from '../../services/adminService'
import { getStudentAccess } from '../../services/systemAccessService'

const QUICK_NAV = [
  { to: '/admin/users', icon: Users, label: 'Manage Users', desc: 'View and manage all platform users' },
  { to: '/admin/subjects', icon: BookOpen, label: 'Manage Subjects', desc: 'Monitor subjects and AI feedback' },
  { to: '/admin/analytics', icon: BarChart3, label: 'Analytics', desc: 'System-wide usage insights and charts' },
]

function unwrapList(res) {
  if (!res) return []
  if (Array.isArray(res)) return res
  if (Array.isArray(res.items)) return res.items
  return []
}

function AdminDashboard() {
  const [users, setUsers] = useState([])
  const [subjectStats, setSubjectStats] = useState([])
  const [activity, setActivity] = useState([])
  const [studentAccessEnabled, setStudentAccessEnabled] = useState(true)

  useEffect(() => {
    let cancelled = false
    Promise.all([
      getUsers({ pageSize: 1000 }).catch(() => null),
      getSubjectStats().catch(() => []),
      getActivityLog(6).catch(() => []),
      getStudentAccess().catch(() => ({ enabled: true })),
    ]).then(([usersRes, statsRes, activityRes, accessRes]) => {
      if (cancelled) return
      setUsers(unwrapList(usersRes))
      setSubjectStats(unwrapList(statsRes))
      setActivity(unwrapList(activityRes))
      setStudentAccessEnabled(Boolean(accessRes?.enabled))
    })
    return () => {
      cancelled = true
    }
  }, [])

  const metrics = useMemo(() => {
    const totalUsers = users.length
    const activeUsers = users.filter((u) => u.status === 'active').length
    const totalSubjects = subjectStats.length
    const totalConversations = subjectStats.reduce((s, x) => s + (x.interactions || 0), 0)
    const totalPositive = subjectStats.reduce((s, x) => s + (x.thumbsUp || 0), 0)
    const totalNegative = subjectStats.reduce((s, x) => s + (x.thumbsDown || 0), 0)
    const totalFeedback = totalPositive + totalNegative
    const satisfactionRate = totalFeedback > 0
      ? Math.round((totalPositive / totalFeedback) * 100)
      : 0

    return [
      { label: 'Total Users', value: totalUsers, icon: Users, accent: 'text-blue-400 bg-blue-400/10' },
      { label: 'Active Users', value: activeUsers, icon: Activity, accent: 'text-emerald-400 bg-emerald-400/10' },
      { label: 'Total Subjects', value: totalSubjects, icon: BookOpen, accent: 'text-amber-400 bg-amber-400/10' },
      { label: 'AI Conversations', value: totalConversations.toLocaleString(), icon: MessageSquare, accent: 'text-purple-400 bg-purple-400/10' },
      { label: 'Satisfaction Rate', value: `${satisfactionRate}%`, icon: ThumbsUp, accent: 'text-dm-primary bg-dm-primary/10' },
    ]
  }, [users, subjectStats])

  return (
    <AdminLayout title="Dashboard">
      <div className="mx-auto max-w-7xl px-6 py-8 flex flex-col gap-8">
        {/* Metrics grid */}
        <motion.section
          className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
          variants={stagger()}
          initial="hidden"
          animate="visible"
        >
          {metrics.map((m) => (
            <MetricCard key={m.label} icon={m.icon} value={m.value} label={m.label} accent={m.accent} />
          ))}
        </motion.section>

        {/* Quick navigation */}
        <motion.section
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35, duration: 0.4 }}
        >
          <h2 className="mb-4 text-lg font-semibold text-dm-foreground">Quick Access</h2>
          <div className="grid gap-4 sm:grid-cols-3">
            {QUICK_NAV.map((item, i) => (
              <motion.div
                key={item.to}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 + i * 0.08 }}
              >
                <Link
                  to={item.to}
                  className="group flex items-start gap-4 rounded-2xl border border-dm-border bg-dm-card p-5 shadow-lg transition-all duration-300 hover:shadow-xl hover:border-dm-primary/40 hover:-translate-y-0.5"
                >
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-dm-primary/10 text-dm-primary transition-colors group-hover:bg-dm-primary/20">
                    <item.icon size={22} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-dm-foreground">{item.label}</span>
                      <ArrowRight size={14} className="text-dm-muted transition-transform group-hover:translate-x-1" />
                    </div>
                    <p className="mt-1 text-sm text-dm-muted">{item.desc}</p>
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>
        </motion.section>

        <motion.div
          className="grid gap-6 lg:grid-cols-2"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.55, duration: 0.4 }}
        >
          {/* System status */}
          <section className={adminCardClass}>
            <h2 className="mb-5 text-lg font-semibold text-dm-foreground">System Status</h2>
            <div className="flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-dm-foreground">Student Access</span>
                <span className="flex items-center gap-2 text-sm">
                  <span
                    className={`h-2 w-2 rounded-full ${studentAccessEnabled ? 'bg-emerald-400 animate-pulse' : 'bg-red-400'}`}
                    aria-hidden
                  />
                  <span className={studentAccessEnabled ? 'text-emerald-400' : 'text-red-400'}>
                    {studentAccessEnabled ? 'Open' : 'Disabled'}
                  </span>
                </span>
              </div>
            </div>
            <Link
              to="/admin/system-access"
              className="mt-4 inline-flex text-sm font-medium text-dm-primary hover:underline"
            >
              Configure student access
            </Link>
          </section>

          {/* Recent activity */}
          <section className={adminCardClass}>
            <h2 className="mb-5 text-lg font-semibold text-dm-foreground">Recent Activity</h2>
            <div className="flex flex-col gap-3">
              {activity.length === 0 ? (
                <p className="text-sm text-dm-muted">No recent activity.</p>
              ) : (
                activity.map((a, i) => (
                  <motion.div
                    key={a.id}
                    initial={{ opacity: 0, x: -12 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.6 + i * 0.06 }}
                    className="flex items-start gap-3 rounded-xl border border-dm-border/50 bg-dm-background/50 px-4 py-3 transition-colors hover:bg-dm-background"
                  >
                    <Clock size={16} className="mt-0.5 shrink-0 text-dm-muted" />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm text-dm-foreground">{a.action}</p>
                      <p className="mt-0.5 text-xs text-dm-muted">
                        {a.user} · {a.time || ''}
                      </p>
                    </div>
                  </motion.div>
                ))
              )}
            </div>
          </section>
        </motion.div>
      </div>
    </AdminLayout>
  )
}

export default AdminDashboard
