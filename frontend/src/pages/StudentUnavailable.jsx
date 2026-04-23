import { motion } from 'framer-motion'
import { Lock } from 'lucide-react'
import GradientBackdrop from '../components/ui/GradientBackdrop'
import PrimaryButton from '../components/ui/PrimaryButton'
import useAuth from '../hooks/useAuth'
import { useStudentAccessGate } from '../hooks/useStudentAccessGate'

function StudentUnavailable() {
  const { logout } = useAuth()
  const { message, loading } = useStudentAccessGate()

  const displayMessage =
    message?.trim() ||
    'Student access is temporarily unavailable (for example during a scheduled exam or maintenance). Please try again later.'

  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden px-6 py-16">
      <GradientBackdrop />
      <motion.div
        className="relative z-10 w-full max-w-md rounded-2xl border border-dm-border bg-dm-card/95 p-8 shadow-2xl shadow-black/30 backdrop-blur-sm"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, ease: 'easeOut' }}
      >
        <div className="mb-6 flex justify-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-amber-500/15 text-amber-400 ring-1 ring-amber-500/30">
            <Lock size={28} aria-hidden />
          </div>
        </div>
        <h1 className="text-center text-xl font-bold text-dm-foreground">Access paused</h1>
        <p className="mt-4 text-center text-sm leading-relaxed text-dm-muted">
          {loading ? 'Loading…' : displayMessage}
        </p>
        <div className="mt-8 flex flex-col gap-3">
          <PrimaryButton type="button" onClick={logout}>
            Sign out
          </PrimaryButton>
        </div>
      </motion.div>
    </div>
  )
}

export default StudentUnavailable
