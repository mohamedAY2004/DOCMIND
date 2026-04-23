import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Loader2 } from 'lucide-react'
import AuthCard from '../components/ui/AuthCard'
import AuthHeader, { UserIcon, LockIcon } from '../components/ui/AuthHeader'
import InputField from '../components/ui/InputField'
import PasswordField from '../components/ui/PasswordField'
import PrimaryButton from '../components/ui/PrimaryButton'
import useAuth from '../hooks/useAuth'
import { getStudentAccess } from '../services/systemAccessService'

const formVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1, delayChildren: 0.2 },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: 'easeOut' } },
}

function Login() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [studentAccessNote, setStudentAccessNote] = useState(null)

  useEffect(() => {
    let cancelled = false
    getStudentAccess().then((data) => {
      if (cancelled || data.enabled) return
      setStudentAccessNote(
        data.message?.trim() ||
          'Student access is currently paused. You can still sign in; student features will be unavailable until access is restored.',
      )
    })
    return () => {
      cancelled = true
    }
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const redirect = await login(username.trim(), password)
      navigate(redirect, { replace: true })
    } catch (err) {
      setError(err.message || 'Invalid username or password.')
      setLoading(false)
    }
  }

  return (
    <AuthCard>
      {studentAccessNote && (
        <div
          className="mb-4 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200/90"
          role="status"
        >
          {studentAccessNote}
        </div>
      )}
      <AuthHeader />
      <motion.form
        className="flex flex-col gap-4"
        onSubmit={handleSubmit}
        variants={formVariants}
        initial="hidden"
        animate="visible"
      >
        <motion.div variants={itemVariants}>
          <InputField
            placeholder="Username"
            icon={<UserIcon />}
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            disabled={loading}
          />
        </motion.div>
        <motion.div variants={itemVariants}>
          <PasswordField
            placeholder="Password"
            icon={<LockIcon />}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            disabled={loading}
          />
        </motion.div>
        {error && (
          <motion.p
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="rounded-lg bg-red-500/10 border border-red-500/20 px-3 py-2 text-sm text-red-400"
          >
            {error}
          </motion.p>
        )}
        <motion.div variants={itemVariants}>
          <PrimaryButton
            type="submit"
            disabled={loading}
            className="mt-2 bg-gradient-to-r from-dm-primary to-dm-primary/80 hover:scale-[1.03] hover:shadow-lg hover:shadow-dm-primary/20 active:scale-95 disabled:opacity-70 disabled:pointer-events-none"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <Loader2 size={18} className="animate-spin" />
                Authenticating&hellip;
              </span>
            ) : (
              'Login'
            )}
          </PrimaryButton>
        </motion.div>
      </motion.form>
    </AuthCard>
  )
}

export default Login
