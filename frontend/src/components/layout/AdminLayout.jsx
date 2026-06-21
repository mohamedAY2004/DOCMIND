import { NavLink, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  LayoutDashboard,
  Users,
  BookOpen,
  CalendarDays,
  BarChart3,
  LogOut,
  Shield,
  Lock,
  GraduationCap,
  MessageSquare,
} from 'lucide-react'
import useAuth from '../../hooks/useAuth'
import { TOP_CHROME_ROW_MIN_CLASS } from '../../constants/layoutChrome'
import ThemeToggle from '../ui/ThemeToggle'
import DocMindLogo from '../ui/DocMindLogo'

const NAV_ITEMS = [
  { to: '/admin', icon: LayoutDashboard, label: 'Dashboard', end: true },
  { to: '/admin/users', icon: Users, label: 'Manage Users' },
  { to: '/admin/instructors', icon: GraduationCap, label: 'Instructors' },
  { to: '/admin/subjects', icon: BookOpen, label: 'Manage Subjects' },
  { to: '/admin/semesters', icon: CalendarDays, label: 'Manage Semesters' },
  { to: '/admin/feedback', icon: MessageSquare, label: 'Feedback & Insights' },
  { to: '/admin/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/admin/system-access', icon: Lock, label: 'System access' },
]

const linkBase =
  'relative flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all duration-200'
const linkInactive =
  'text-dm-muted hover:bg-dm-background hover:text-dm-foreground'
const linkActive =
  'text-dm-foreground'

const pageVariants = {
  initial: { opacity: 0, y: 8 },
  enter: { opacity: 1, y: 0, transition: { duration: 0.3, ease: 'easeOut' } },
  exit: { opacity: 0, y: -8, transition: { duration: 0.2 } },
}

function AdminLayout({ children, title }) {
  const { logout } = useAuth()
  const location = useLocation()

  return (
    <div className="flex h-screen overflow-hidden bg-dm-background">
      {/* Sidebar */}
      <aside className="hidden lg:flex w-64 shrink-0 flex-col border-r border-dm-border bg-dm-card">
        {/* Brand */}
        <div
          className={`flex items-center gap-3 border-b border-dm-border/50 px-5 py-4 ${TOP_CHROME_ROW_MIN_CLASS}`}
        >
          <DocMindLogo alt="" className="h-10 w-auto object-contain" />
          <div className="min-w-0">
            <span className="block text-base font-semibold text-dm-foreground">DocMind</span>
            <span className="flex items-center gap-1 text-xs text-dm-primary">
              <Shield size={11} />
              Admin Panel
            </span>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto p-3 flex flex-col gap-1">
          {NAV_ITEMS.map(({ to, icon: Icon, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `${linkBase} ${isActive ? linkActive : linkInactive}`
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <motion.div
                      layoutId="admin-nav-pill"
                      className="absolute inset-0 rounded-xl bg-dm-primary/15 shadow-sm shadow-dm-primary/10"
                      transition={{ type: 'spring', stiffness: 350, damping: 30 }}
                    />
                  )}
                  <Icon size={20} className="relative shrink-0" />
                  <span className="relative">{label}</span>
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="shrink-0 border-t border-dm-border/50 p-3 flex flex-col gap-1">
          <div className="flex items-center gap-3 rounded-xl px-4 py-2">
            <ThemeToggle />
            <span className="text-sm text-dm-muted">Theme</span>
          </div>
          <button
            type="button"
            onClick={logout}
            className="flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all duration-200 text-dm-muted hover:bg-dm-background hover:text-dm-foreground w-full"
          >
            <LogOut size={20} className="shrink-0" />
            Log out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 min-w-0 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header
          className={`shrink-0 flex items-center justify-between border-b border-dm-border bg-dm-card px-6 py-4 ${TOP_CHROME_ROW_MIN_CLASS}`}
        >
          <div className="flex items-center gap-3 lg:hidden">
            <DocMindLogo alt="" className="h-8 w-auto object-contain" />
            <span className="text-sm font-semibold text-dm-foreground">DocMind Admin</span>
          </div>
          {title && (
            <h1 className="text-xl font-bold text-dm-foreground">{title}</h1>
          )}
          <div className="flex items-center gap-1">
            <ThemeToggle />
            <button
              type="button"
              onClick={logout}
              className="lg:hidden flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-dm-muted hover:bg-dm-background hover:text-dm-foreground transition-colors"
            >
              <LogOut size={16} />
            </button>
          </div>
        </header>

        {/* Page content with exit/enter animation */}
        <div className="flex-1 min-h-0 overflow-y-auto">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              variants={pageVariants}
              initial="initial"
              animate="enter"
              exit="exit"
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  )
}

export default AdminLayout
