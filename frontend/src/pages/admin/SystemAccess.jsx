import { useCallback, useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import { Lock, Save } from 'lucide-react'
import AdminLayout from '../../components/layout/AdminLayout'
import PrimaryButton from '../../components/ui/PrimaryButton'
import { adminCardClass } from '../../utils/motion'
import { getStudentAccess, setStudentAccess } from '../../services/systemAccessService'

const MAX_MSG_LENGTH = 300

function SystemAccess() {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [enabled, setEnabled] = useState(true)
  const [message, setMessage] = useState('')
  const [updatedAt, setUpdatedAt] = useState(null)
  const msgTooLong = message.length > MAX_MSG_LENGTH

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await getStudentAccess()
      setEnabled(data.enabled)
      setMessage(data.message || '')
      setUpdatedAt(data.updatedAt)
    } catch {
      toast.error('Could not load student access settings.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (msgTooLong) return
    setSaving(true)
    try {
      const data = await setStudentAccess({ enabled, message: message.trim() })
      setUpdatedAt(data.updatedAt)
      toast.success(
        data.enabled ? 'Students can use the platform.' : 'Student access is now disabled.',
      )
    } catch {
      toast.error('Could not save settings.')
    } finally {
      setSaving(false)
    }
  }

  const updatedLabel = updatedAt
    ? new Date(updatedAt).toLocaleString(undefined, {
        dateStyle: 'medium',
        timeStyle: 'short',
      })
    : 'Never'

  return (
    <AdminLayout title="Student access">
      <div className="mx-auto max-w-2xl px-6 py-8">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35 }}
          className={adminCardClass}
        >
          <div className="mb-6 flex items-start gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-dm-primary/10 text-dm-primary">
              <Lock size={24} aria-hidden />
            </div>
            <div className="min-w-0 flex-1">
              <h2 className="text-lg font-semibold text-dm-foreground">Student access</h2>
              <p className="mt-1 text-sm text-dm-muted">
                When disabled, students see a full-screen message and cannot use student features.
                Instructors and admins are not affected. Enforce the same rules on your API (403
                with code STUDENT_ACCESS_DISABLED).
              </p>
            </div>
          </div>

          {loading ? (
            <p className="text-sm text-dm-muted">Loading…</p>
          ) : (
            <form className="flex flex-col gap-6" onSubmit={handleSubmit}>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <span className="block text-sm font-medium text-dm-foreground">
                    Allow student access
                  </span>
                  <span className="text-xs text-dm-muted">Turn off during exams or maintenance</span>
                </div>
                <button
                  type="button"
                  role="switch"
                  aria-checked={enabled}
                  onClick={() => setEnabled((v) => !v)}
                  className={`relative inline-flex h-9 w-16 shrink-0 cursor-pointer rounded-full border border-dm-border transition-colors focus:outline-none focus:ring-2 focus:ring-dm-primary focus:ring-offset-2 focus:ring-offset-dm-card ${
                    enabled ? 'bg-emerald-500/30' : 'bg-dm-background'
                  }`}
                >
                  <span
                    className={`pointer-events-none absolute top-1 left-1 flex h-7 w-7 rounded-full bg-dm-foreground shadow transition-transform ${
                      enabled ? 'translate-x-7 bg-emerald-400' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>

              <div className="flex flex-col gap-2">
                <label htmlFor="student-access-message" className="text-sm font-medium text-dm-foreground">
                  Message for students (optional)
                </label>
                <textarea
                  id="student-access-message"
                  rows={4}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="e.g. The platform is closed until 3:00 PM for exams."
                  className={`w-full resize-y rounded-xl border bg-dm-background px-4 py-3 text-sm text-dm-foreground placeholder:text-dm-muted/70 focus:outline-none focus:ring-2 ${msgTooLong ? 'border-red-500/60 focus:border-red-500/60 focus:ring-red-500/20' : 'border-dm-border focus:border-dm-primary/50 focus:ring-dm-primary/20'}`}
                />
                <div className="flex items-center justify-between">
                  {msgTooLong ? (
                    <p className="text-xs text-red-400">Message is too long. Please shorten it.</p>
                  ) : (
                    <span />
                  )}
                  <span className={`ml-auto text-xs ${msgTooLong ? 'text-red-400 font-medium' : 'text-dm-muted'}`}>
                    {message.length} / {MAX_MSG_LENGTH}
                  </span>
                </div>
              </div>

              <p className="text-xs text-dm-muted">Last saved: {updatedLabel}</p>

              <PrimaryButton type="submit" disabled={saving || msgTooLong} fullWidth={false} className="sm:w-auto sm:self-start">
                {saving ? (
                  'Saving…'
                ) : (
                  <span className="flex items-center justify-center gap-2">
                    <Save size={18} aria-hidden />
                    Save settings
                  </span>
                )}
              </PrimaryButton>
            </form>
          )}
        </motion.div>
      </div>
    </AdminLayout>
  )
}

export default SystemAccess
