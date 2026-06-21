import { useEffect, useState } from 'react'
import { Loader2, Save, CalendarPlus } from 'lucide-react'
import { toast } from 'sonner'
import Modal from './Modal'
import { primaryButtonCompactClass } from '../../constants/themeClasses'
import FormField, { inputClass } from './FormField'
import { createSemester, updateSemester } from '../../services/adminService'

const ID_RE = /^[a-z0-9-]{2,64}$/

const DEFAULT_FORM = {
  id: '',
  label: '',
  sortOrder: 0,
  startDate: '',
  endDate: '',
}

function errorMessage(err, fallback) {
  const data = err?.response?.data
  if (data?.message) return data.message
  if (data?.code) return data.code
  return fallback
}

function SemesterFormModal({ open, onClose, mode = 'create', semester = null, onSaved }) {
  const [form, setForm] = useState(DEFAULT_FORM)
  const [submitting, setSubmitting] = useState(false)
  const [errors, setErrors] = useState({})

  const isEdit = mode === 'edit'

  useEffect(() => {
    if (!open) return
    setErrors({})
    if (isEdit && semester) {
      setForm({
        id: semester.id || '',
        label: semester.label || '',
        sortOrder: semester.sortOrder ?? 0,
        startDate: semester.startDate || '',
        endDate: semester.endDate || '',
      })
    } else {
      setForm(DEFAULT_FORM)
    }
  }, [open, isEdit, semester])

  const validate = () => {
    const e = {}
    if (!isEdit) {
      const id = form.id.trim()
      if (!id) {
        e.id = 'Semester id is required.'
      } else if (!ID_RE.test(id)) {
        e.id = 'Lowercase letters, numbers, and hyphens only (2–64 characters).'
      }
    }
    if (!form.label.trim()) {
      e.label = 'Label is required.'
    } else if (form.label.trim().length > 120) {
      e.label = 'At most 120 characters.'
    }
    if (form.startDate && form.endDate && form.endDate < form.startDate) {
      e.endDate = 'End date must be on or after the start date.'
    }
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = async (evt) => {
    evt.preventDefault()
    if (!validate()) return
    setSubmitting(true)
    try {
      const common = {
        label: form.label.trim(),
        sortOrder: Number(form.sortOrder) || 0,
        startDate: form.startDate || null,
        endDate: form.endDate || null,
      }
      if (isEdit) {
        const updated = await updateSemester(semester.id, common)
        toast.success(`${updated.label} updated`)
        onSaved?.(updated)
      } else {
        const created = await createSemester({ id: form.id.trim(), ...common })
        toast.success(`${created.label} created`)
        onSaved?.(created)
      }
      onClose?.()
    } catch (err) {
      const code = err?.response?.data?.code
      if (code === 'CONFLICT') {
        setErrors({ id: 'A semester with this id already exists.' })
      } else {
        toast.error(errorMessage(err, 'Could not save semester.'))
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Modal
      open={open}
      onClose={submitting ? undefined : onClose}
      title={isEdit ? `Edit semester — ${semester?.label || ''}` : 'Add semester'}
      size="md"
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <FormField
            label="Semester id"
            required={!isEdit}
            hint={isEdit ? 'Cannot be changed after creation' : 'e.g. fall-2025'}
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
              placeholder="fall-2025"
            />
          </FormField>

          <FormField label="Sort order" hint="Higher shows first">
            <input
              type="number"
              value={form.sortOrder}
              onChange={(e) =>
                setForm((f) => ({ ...f, sortOrder: e.target.value }))
              }
              className={inputClass}
            />
          </FormField>
        </div>

        <FormField label="Label" required error={errors.label} hint="Shown to users, e.g. Fall 2025">
          <input
            type="text"
            value={form.label}
            onChange={(e) => setForm((f) => ({ ...f, label: e.target.value }))}
            className={inputClass}
            placeholder="Fall 2025"
            maxLength={120}
          />
        </FormField>

        <div className="grid gap-4 sm:grid-cols-2">
          <FormField label="Start date" hint="Optional — term opens">
            <input
              type="date"
              value={form.startDate}
              onChange={(e) =>
                setForm((f) => ({ ...f, startDate: e.target.value }))
              }
              className={inputClass}
            />
          </FormField>

          <FormField label="End date" hint="Optional — term archives after" error={errors.endDate}>
            <input
              type="date"
              value={form.endDate}
              onChange={(e) =>
                setForm((f) => ({ ...f, endDate: e.target.value }))
              }
              className={inputClass}
            />
          </FormField>
        </div>

        <p className="rounded-xl border border-dm-border/60 bg-dm-background/60 px-3 py-2 text-[11px] leading-relaxed text-dm-muted">
          The lifecycle state (upcoming / active / archived) is derived from these
          dates automatically — leaving them empty keeps the term permanently active.
        </p>

        <div className="mt-2 flex items-center justify-end gap-2 border-t border-dm-border/60 pt-4">
          <button
            type="button"
            onClick={onClose}
            disabled={submitting}
            className="rounded-xl border border-dm-border bg-dm-card px-4 py-2 text-sm font-medium text-dm-muted transition-colors hover:bg-dm-background hover:text-dm-foreground disabled:opacity-50"
          >
            Cancel
          </button>
          <button type="submit" disabled={submitting} className={primaryButtonCompactClass}>
            {submitting ? (
              <Loader2 size={14} className="animate-spin" />
            ) : isEdit ? (
              <Save size={14} />
            ) : (
              <CalendarPlus size={14} />
            )}
            {isEdit ? 'Save changes' : 'Create semester'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

export default SemesterFormModal
