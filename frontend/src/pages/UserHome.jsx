import { motion } from 'framer-motion'
import { FileText, GraduationCap, LogOut } from 'lucide-react'
import { AppLayout, AppTopBar } from '../components/layout'
import ActionCard from '../components/ui/ActionCard'
import GradientBackdrop from '../components/ui/GradientBackdrop'
import PageFooter from '../components/ui/PageFooter'
import ThemeToggle from '../components/ui/ThemeToggle'
import useAuth from '../hooks/useAuth'

const logoutBtnClass =
  'ml-auto flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-dm-muted hover:bg-dm-background hover:text-dm-foreground transition-colors'

function UserHome() {
  const { user, logout } = useAuth()
  const userName = user?.name || user?.username || 'Student'

  return (
    <AppLayout
      topNav={
        <AppTopBar title="DocMind" showLogo logoClassName="h-14 w-auto object-contain" logoHref="/home">
          <div className="ml-auto flex items-center gap-1">
            <ThemeToggle />
            <button type="button" onClick={logout} className={logoutBtnClass} aria-label="Log out">
              <LogOut size={18} className="shrink-0 text-current" />
              Log out
            </button>
          </div>
        </AppTopBar>
      }
    >
      <div className="relative flex flex-1 flex-col min-h-0">
        <GradientBackdrop variant="default" />

        <div className="relative flex-1 flex items-center justify-center px-4 md:px-6">
          <div className="w-full max-w-4xl">
            <motion.section
              className="text-center"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: 'easeOut' }}
            >
              <h1 className="text-4xl font-extrabold tracking-tight text-dm-foreground md:text-5xl">
                Welcome, {userName}!
              </h1>
              <p className="mt-3 text-base text-dm-muted/80 md:text-lg">
                How can I help you with your studies today?
              </p>
            </motion.section>

            <div className="mt-10 grid gap-8 sm:grid-cols-2">
              <motion.div
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.15, duration: 0.5, ease: 'easeOut' }}
              >
                <ActionCard
                  icon={<FileText size={36} className="text-dm-primary" />}
                  title="Chat with Doc."
                  description="Upload your documents, lecture notes, or textbook PDFs to get instant, context-aware answers and summaries."
                  buttonText="Start Chatting →"
                  href="/chat"
                />
              </motion.div>
              <motion.div
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.25, duration: 0.5, ease: 'easeOut' }}
              >
                <ActionCard
                  icon={<GraduationCap size={36} className="text-dm-primary" />}
                  title="Chat with Tutors"
                  description="Engage with AI tutors specialized in various subjects like Chemistry, History, or Computer Science for targeted help."
                  buttonText="Explore Tutors →"
                  href="/tutors"
                />
              </motion.div>
            </div>
          </div>
        </div>

        <PageFooter />
      </div>
    </AppLayout>
  )
}

export default UserHome
