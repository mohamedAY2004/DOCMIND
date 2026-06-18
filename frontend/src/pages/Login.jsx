import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Loader2 } from 'lucide-react'
import AuthCard from '../components/ui/AuthCard'
import AuthHeader, { UserIcon, LockIcon } from '../components/ui/AuthHeader'
import InputField from '../components/ui/InputField'
import PasswordField from '../components/ui/PasswordField'
import PrimaryButton from '../components/ui/PrimaryButton'
import ThemeToggle from '../components/ui/ThemeToggle'
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
  const [fieldErrors, setFieldErrors] = useState({})
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

    const fe = {}
    if (!username.trim()) fe.username = 'Username is required.'
    if (!password) fe.password = 'Password is required.'
    if (Object.keys(fe).length > 0) {
      setFieldErrors(fe)
      return
    }
    setFieldErrors({})
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
      <div className="absolute top-4 right-4 z-10">
        <ThemeToggle />
      </div>
      {studentAccessNote && (
        <div
          className="mb-4 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-600"
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
        <motion.div variants={itemVariants} className="flex flex-col gap-1">
          <InputField
            placeholder="Username"
            icon={<UserIcon />}
            value={username}
            onChange={(e) => { setUsername(e.target.value); setFieldErrors((fe) => ({ ...fe, username: undefined })) }}
            autoComplete="username"
            disabled={loading}
            className={fieldErrors.username ? 'border-red-500/60 focus-within:border-red-500/80 focus-within:ring-red-500/20' : ''}
          />
          {fieldErrors.username && (
            <p className="pl-1 text-xs text-red-400">{fieldErrors.username}</p>
          )}
        </motion.div>
        <motion.div variants={itemVariants} className="flex flex-col gap-1">
          <PasswordField
            placeholder="Password"
            icon={<LockIcon />}
            value={password}
            onChange={(e) => { setPassword(e.target.value); setFieldErrors((fe) => ({ ...fe, password: undefined })) }}
            autoComplete="current-password"
            disabled={loading}
            className={fieldErrors.password ? 'border-red-500/60 focus-within:border-red-500/80 focus-within:ring-red-500/20' : ''}
          />
          {fieldErrors.password && (
            <p className="pl-1 text-xs text-red-400">{fieldErrors.password}</p>
          )}
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
