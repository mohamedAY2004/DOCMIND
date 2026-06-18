import { useEffect, useMemo, useState } from 'react'
import { Loader2, Save, UserPlus } from 'lucide-react'
import { toast } from 'sonner'
import Modal from './Modal'
import { primaryButtonCompactClass } from '../../constants/themeClasses'
import FormField, { inputClass, selectClass } from './FormField'
import MultiSelect from './MultiSelect'
import {
  createUser,
  getUserSubjects,
  listSubjects,
  updateUser,
} from '../../services/adminService'

const ROLE_OPTIONS = [
  { value: 'student', label: 'Student' },
  { value: 'instructor', label: 'Instructor' },
  { value: 'admin', label: 'Admin' },
]

const DEFAULT_FORM = {
  username: '',
  name: '',
  email: '',
  role: 'student',
  password: '',
}

function unwrapList(res) {
  if (!res) return []
  if (Array.isArray(res)) return res
  if (Array.isArray(res.items)) return res.items
  return []
}

function errorMessage(err, fallback) {
  const data = err?.response?.data
  if (data?.message) return data.message
  if (data?.code) return data.code
  return fallback
}

function UserFormModal({
  open,
  onClose,
  mode = 'create',
  user = null,
  lockedRole = null,
  onSaved,
}) {
  const [form, setForm] = useState(DEFAULT_FORM)
  const [enrolledIds, setEnrolledIds] = useState([])
  const [subjects, setSubjects] = useState([])
  const [loadingSubjects, setLoadingSubjects] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [errors, setErrors] = useState({})

  const isEdit = mode === 'edit'

  useEffect(() => {
    if (!open) return
    setErrors({})
    if (isEdit && user) {
      setForm({
        username: user.username || '',
        name: user.name || '',
        email: user.email || '',
        role: user.role || 'student',
        password: '',
      })
    } else {
      setForm({ ...DEFAULT_FORM, role: lockedRole || DEFAULT_FORM.role })
      setEnrolledIds([])
    }
  }, [open, isEdit, user, lockedRole])

  useEffect(() => {
    if (!open) return
    let cancelled = false
    setLoadingSubjects(true)
    listSubjects({ pageSize: 1000 })
      .then((res) => {
        if (!cancelled) setSubjects(unwrapList(res))
      })
      .catch(() => {
        if (!cancelled) setSubjects([])
      })
      .finally(() => {
        if (!cancelled) setLoadingSubjects(false)
      })
    return () => {
      cancelled = true
    }
  }, [open])

  useEffect(() => {
    if (!open || !isEdit || !user) return
    if (user.role !== 'student') {
      setEnrolledIds([])
      return
    }
    let cancelled = false
    getUserSubjects(user.id)
      .then((res) => {
        if (cancelled) return
        setEnrolledIds((res || []).map((s) => s.id))
      })
      .catch(() => {
        if (!cancelled) setEnrolledIds([])
      })
    return () => {
      cancelled = true
    }
  }, [open, isEdit, user])

  const subjectOptions = useMemo(
    () =>
      subjects.map((s) => ({
        id: s.id,
        label: s.title,
        sub: s.courseCode,
      })),
    [subjects],
  )

  const showEnrollment = form.role === 'student'

  const validate = () => {
    const e = {}
    if (!isEdit) {
      const u = form.username.trim()
      if (!u) {
        e.username = 'Username is required.'
      } else if (u.length < 3) {
        e.username = 'At least 3 characters.'
      } else if (u.length > 30) {
        e.username = 'At most 30 characters.'
      } else if (!/^[a-z0-9_-]+$/.test(u)) {
        e.username = 'Only lowercase letters, numbers, underscores, and hyphens.'
      }
      const pwd = form.password || ''
      if (pwd.length < 8) {
        e.password = 'At least 8 characters.'
      } else if (!/[a-zA-Z]/.test(pwd)) {
        e.password = 'Must contain at least one letter.'
      } else if (!/[0-9]/.test(pwd)) {
        e.password = 'Must contain at least one number.'
      }
    }
    const name = form.name.trim()
    if (!name) {
      e.name = 'Full name is required.'
    } else if (name.length > 100) {
      e.name = 'At most 100 characters.'
    }
    if (!form.email.trim()) {
      e.email = 'Email is required.'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) {
      e.email = 'Enter a valid email address.'
    }
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = async (evt) => {
    evt.preventDefault()
    if (!validate()) return
    setSubmitting(true)
    try {
      if (isEdit) {
        const patch = {
          name: form.name.trim(),
          email: form.email.trim(),
          role: form.role,
        }
        if (form.role === 'student') {
          patch.enrolledSubjectIds = enrolledIds
        }
        const updated = await updateUser(user.id, patch)
        toast.success(`${updated.name} updated`)
        onSaved?.(updated)
      } else {
        const body = {
          username: form.username.trim(),
          name: form.name.trim(),
          email: form.email.trim(),
          role: form.role,
          password: form.password,
        }
        if (form.role === 'student' && enrolledIds.length > 0) {
          body.enrolledSubjectIds = enrolledIds
        }
        const created = await createUser(body)
        toast.success(`${created.name} created`)
        onSaved?.(created)
      }
      onClose?.()
    } catch (err) {
      const code = err?.response?.data?.code
      if (code === 'USERNAME_TAKEN') {
        setErrors({ username: 'Username already exists' })
      } else if (code === 'EMAIL_TAKEN') {
        setErrors({ email: 'Email already in use' })
      } else {
        toast.error(errorMessage(err, 'Could not save user.'))
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Modal
      open={open}
      onClose={submitting ? undefined : onClose}
      title={isEdit ? `Edit user — ${user?.name || ''}` : 'Add user'}
      size="lg"
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <FormField label="Full name" required error={errors.name}>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              className={inputClass}
              placeholder="Ada Lovelace"
            />
          </FormField>

          <FormField label="Email" required error={errors.email}>
            <input
              type="email"
              value={form.email}
              onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
              className={inputClass}
              placeholder="user@example.com"
            />
          </FormField>

          <FormField
            label="Username"
            required={!isEdit}
            hint={isEdit ? 'Usernames cannot be changed' : '3–30 chars · lowercase letters, numbers, _ or -'}
            error={errors.username}
          >
            <input
              type="text"
              value={form.username}
              onChange={(e) =>
                setForm((f) => ({ ...f, username: e.target.value }))
              }
              disabled={isEdit}
              className={inputClass}
              placeholder="ada"
            />
          </FormField>

          <FormField label="Role" required>
            <select
              value={form.role}
              onChange={(e) =>
                setForm((f) => ({ ...f, role: e.target.value }))
              }
              disabled={!!lockedRole}
              className={selectClass}
            >
              {ROLE_OPTIONS.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
          </FormField>

          {!isEdit && (
            <FormField
              label="Password"
              required
              hint="Min 8 characters · must include a letter and a number"
              error={errors.password}
            >
              <input
                type="password"
                value={form.password}
                onChange={(e) =>
                  setForm((f) => ({ ...f, password: e.target.value }))
                }
                className={inputClass}
                placeholder="••••••••"
              />
            </FormField>
          )}
        </div>

        {showEnrollment && (
          <FormField
            label="Enrolled subjects"
            hint={loadingSubjects ? 'Loading subjects…' : 'Optional — assign later too'}
          >
            <MultiSelect
              options={subjectOptions}
              value={enrolledIds}
              onChange={setEnrolledIds}
              placeholder="Pick subjects…"
              emptyLabel="No subjects available"
              disabled={loadingSubjects}
            />
          </FormField>
        )}

        <div className="mt-2 flex items-center justify-end gap-2 border-t border-dm-border/60 pt-4">
          <button
            type="button"
            onClick={onClose}
            disabled={submitting}
            className="rounded-xl border border-dm-border bg-dm-card px-4 py-2 text-sm font-medium text-dm-muted transition-colors hover:bg-dm-background hover:text-dm-foreground disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={submitting}
            className={primaryButtonCompactClass}
          >
            {submitting ? (
              <Loader2 size={14} className="animate-spin" />
            ) : isEdit ? (
              <Save size={14} />
            ) : (
              <UserPlus size={14} />
            )}
            {isEdit ? 'Save changes' : 'Create user'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

export default UserFormModal
