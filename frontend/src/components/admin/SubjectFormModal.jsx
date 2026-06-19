import { useEffect, useMemo, useState } from 'react'
import { Loader2, Save, BookPlus } from 'lucide-react'
import { toast } from 'sonner'
import Modal from './Modal'
import { primaryButtonCompactClass } from '../../constants/themeClasses'
import FormField, { inputClass, selectClass, textareaClass } from './FormField'
import MultiSelect from './MultiSelect'
import {
  createSubject,
  getSemesters,
  getUsers,
  updateSubject,
} from '../../services/adminService'

const SLUG_RE = /^[a-z0-9-]{2,64}$/
const COURSE_CODE_RE = /^[A-Z0-9-]{2,20}$/

const DEFAULT_FORM = {
  id: '',
  title: '',
  description: '',
  courseCode: '',
  semesterId: '',
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

function SubjectFormModal({
  open,
  onClose,
  mode = 'create',
  subject = null,
  onSaved,
}) {
  const [form, setForm] = useState(DEFAULT_FORM)
  const [instructorIds, setInstructorIds] = useState([])
  const [superInstructorId, setSuperInstructorId] = useState('')
  const [studentIds, setStudentIds] = useState([])
  const [semesters, setSemesters] = useState([])
  const [instructors, setInstructors] = useState([])
  const [students, setStudents] = useState([])
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [errors, setErrors] = useState({})

  const isEdit = mode === 'edit'

  useEffect(() => {
    if (!open) return
    setErrors({})
    if (isEdit && subject) {
      setForm({
        id: subject.id || '',
        title: subject.title || '',
        description: subject.description || '',
        courseCode: subject.courseCode || '',
        semesterId: subject.semesterId || subject.semester || '',
      })
      setInstructorIds(subject.instructorIds || [])
      setSuperInstructorId(subject.superInstructorId || subject.instructorIds?.[0] || '')
      setStudentIds(subject.studentIds || [])
    } else {
      setForm(DEFAULT_FORM)
      setInstructorIds([])
      setSuperInstructorId('')
      setStudentIds([])
    }
  }, [open, isEdit, subject])

  useEffect(() => {
    if (!open) return
    let cancelled = false
    setLoading(true)
    Promise.all([
      getSemesters().catch(() => []),
      getUsers({ role: 'instructor', pageSize: 1000 }).catch(() => null),
      getUsers({ role: 'student', pageSize: 1000 }).catch(() => null),
    ])
      .then(([semsRes, insRes, stuRes]) => {
        if (cancelled) return
        setSemesters(unwrapList(semsRes))
        setInstructors(unwrapList(insRes).filter((u) => u.role === 'instructor'))
        setStudents(unwrapList(stuRes).filter((u) => u.role === 'student'))
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [open])

  const instructorOptions = useMemo(
    () =>
      instructors.map((u) => ({
        id: u.id,
        label: u.name,
        sub: u.email,
      })),
    [instructors],
  )

  const studentOptions = useMemo(
    () =>
      students.map((u) => ({
        id: u.id,
        label: u.name,
        sub: u.email,
      })),
    [students],
  )

  const handleInstructorIdsChange = (ids) => {
    setInstructorIds(ids)
    // Keep superInstructorId in sync: if the current super is removed, default
    // to the first remaining instructor.
    setSuperInstructorId((prev) => {
      if (ids.includes(prev)) return prev
      return ids[0] || ''
    })
  }

  const validate = () => {
    const e = {}
    if (!isEdit) {
      if (!form.id.trim()) {
        e.id = 'Subject ID is required.'
      } else if (!SLUG_RE.test(form.id.trim())) {
        e.id = 'Lowercase letters, numbers, and hyphens only (2–64 characters).'
      }
    }
    const title = form.title.trim()
    if (!title) {
      e.title = 'Title is required.'
    } else if (title.length > 120) {
      e.title = 'At most 120 characters.'
    }
    const desc = form.description.trim()
    if (!desc) {
      e.description = 'Description is required.'
    } else if (desc.length < 10) {
      e.description = 'At least 10 characters.'
    }
    const code = form.courseCode.trim().toUpperCase()
    if (!code) {
      e.courseCode = 'Course code is required.'
    } else if (!COURSE_CODE_RE.test(code)) {
      e.courseCode = 'Uppercase letters, numbers, and hyphens only (2–20 characters).'
    }
    if (instructorIds.length === 0) {
      e.instructors = 'At least one instructor must be assigned.'
    } else if (!superInstructorId || !instructorIds.includes(superInstructorId)) {
      e.superInstructor = 'You must designate a super instructor from the assigned list.'
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
          title: form.title.trim(),
          description: form.description.trim(),
          courseCode: form.courseCode.trim(),
          semesterId: form.semesterId || null,
          instructorIds,
          superInstructorId,
          studentIds,
        }
        const updated = await updateSubject(subject.id, patch)
        toast.success(`${updated.title} updated`)
        onSaved?.(updated)
      } else {
        const body = {
          id: form.id.trim(),
          title: form.title.trim(),
          description: form.description.trim(),
          courseCode: form.courseCode.trim(),
          instructorIds,
          superInstructorId,
          studentIds,
        }
        if (form.semesterId) body.semesterId = form.semesterId
        const created = await createSubject(body)
        toast.success(`${created.title} created`)
        onSaved?.(created)
      }
      onClose?.()
    } catch (err) {
      const code = err?.response?.data?.code
      if (code === 'CONFLICT') {
        setErrors({ id: 'Subject id already exists' })
      } else if (code === 'VALIDATION_ERROR') {
        toast.error(
          err?.response?.data?.message ||
            'Invalid instructor or student in the roster.',
        )
      } else {
        toast.error(errorMessage(err, 'Could not save subject.'))
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Modal
      open={open}
      onClose={submitting ? undefined : onClose}
      title={isEdit ? `Edit subject — ${subject?.title || ''}` : 'Add subject'}
      size="xl"
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <FormField
            label="Subject id (slug)"
            required={!isEdit}
            hint={
              isEdit
                ? 'Cannot be changed after creation'
                : 'Lowercase letters, numbers, and hyphens'
            }
            error={errors.id}
          >
            <input
              type="text"
              value={form.id}
              onChange={(e) =>
                setForm((f) => ({ ...f, id: e.target.value.toLowerCase() }))
              }
              disabled={isEdit}
              className={inputClass}
              placeholder="calc-ii"
            />
          </FormField>

          <FormField label="Course code" required error={errors.courseCode} hint="Uppercase letters, numbers, hyphens">
            <input
              type="text"
              value={form.courseCode}
              onChange={(e) =>
                setForm((f) => ({ ...f, courseCode: e.target.value.toUpperCase() }))
              }
              className={inputClass}
              placeholder="MATH-102"
              maxLength={20}
            />
          </FormField>

          <FormField label="Title" required error={errors.title} hint="Up to 120 characters">
            <input
              type="text"
              value={form.title}
              onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
              className={inputClass}
              placeholder="Calculus II"
              maxLength={120}
            />
          </FormField>

          <FormField label="Semester" hint="Optional">
            <select
              value={form.semesterId || ''}
              onChange={(e) =>
                setForm((f) => ({ ...f, semesterId: e.target.value }))
              }
              className={selectClass}
            >
              <option value="">No semester</option>
              {semesters.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.label}
                </option>
              ))}
            </select>
          </FormField>
        </div>

        <FormField label="Description" required error={errors.description} hint="10–500 characters">
          <textarea
            value={form.description}
            onChange={(e) =>
              setForm((f) => ({ ...f, description: e.target.value }))
            }
            className={textareaClass}
            placeholder="What this subject is about…"
            maxLength={500}
          />
        </FormField>

        <FormField
          label="Instructors"
          required
          hint={loading ? 'Loading users…' : 'Pick one or more instructors'}
          error={errors.instructors}
        >
          <MultiSelect
            options={instructorOptions}
            value={instructorIds}
            onChange={handleInstructorIdsChange}
            placeholder="Pick instructors…"
            emptyLabel="No instructors available"
            disabled={loading}
          />
        </FormField>

        {instructorIds.length > 0 && (
          <FormField
            label="Super instructor"
            required
            hint="This instructor can upload and delete materials"
            error={errors.superInstructor}
          >
            <select
              value={superInstructorId}
              onChange={(e) => setSuperInstructorId(e.target.value)}
              className={selectClass}
            >
              <option value="">— select super instructor —</option>
              {instructorIds.map((id) => {
                const ins = instructors.find((u) => u.id === id)
                return (
                  <option key={id} value={id}>
                    {ins?.name || id}
                  </option>
                )
              })}
            </select>
          </FormField>
        )}

        <FormField
          label="Enrolled students"
          hint={loading ? 'Loading users…' : 'Optional — you can edit later'}
        >
          <MultiSelect
            options={studentOptions}
            value={studentIds}
            onChange={setStudentIds}
            placeholder="Pick students…"
            emptyLabel="No students available"
            disabled={loading}
          />
        </FormField>

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
              <BookPlus size={14} />
            )}
            {isEdit ? 'Save changes' : 'Create subject'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

export default SubjectFormModal
