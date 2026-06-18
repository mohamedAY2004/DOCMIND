import { useCallback, useEffect, useMemo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
import {
  Search,
  UserPlus,
  GraduationCap,
  BookOpen,
  Plus,
  X,
  Loader2,
  Mail,
  ChevronDown,
} from 'lucide-react'
import AdminLayout from '../../components/layout/AdminLayout'
import { primaryButtonCompactClass } from '../../constants/themeClasses'
import UserFormModal from '../../components/admin/UserFormModal'
import ConfirmDialog from '../../components/admin/ConfirmDialog'
import Modal from '../../components/admin/Modal'
import FormField, { selectClass } from '../../components/admin/FormField'
import {
  deleteUser,
  getUsers,
  listSubjects,
  setUserStatus,
  updateSubject,
} from '../../services/adminService'
import { stagger, fadeUp, adminCardClass } from '../../utils/motion'

function unwrapList(res) {
  if (!res) return []
  if (Array.isArray(res)) return res
  if (Array.isArray(res.items)) return res.items
  return []
}

function statusBadge(status) {
  return status === 'active'
    ? 'bg-emerald-400/10 text-emerald-400'
    : 'bg-red-400/10 text-red-400'
}

function AssignSubjectDialog({ open, onClose, instructor, available, onAssigned }) {
  const [subjectId, setSubjectId] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (open) setSubjectId(available[0]?.id || '')
  }, [open, available])

  const handleAssign = async () => {
    if (!subjectId) return
    setBusy(true)
    try {
      const subject = available.find((s) => s.id === subjectId)
      const next = [...(subject?.instructorIds || []), instructor.id]
      const updated = await updateSubject(subjectId, {
        instructorIds: Array.from(new Set(next)),
      })
      toast.success(`${instructor.name} assigned to ${updated.title}`)
      onAssigned?.(updated)
      onClose?.()
    } catch (err) {
      toast.error(
        err?.response?.data?.message || 'Could not assign instructor.',
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal
      open={open}
      onClose={busy ? undefined : onClose}
      title={`Assign ${instructor?.name || ''} to a subject`}
      size="md"
    >
      <div className="flex flex-col gap-4">
        <FormField label="Subject">
          <select
            value={subjectId}
            onChange={(e) => setSubjectId(e.target.value)}
            disabled={busy || available.length === 0}
            className={selectClass}
          >
            {available.length === 0 ? (
              <option value="">No subjects left to assign</option>
            ) : (
              available.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.title} ({s.courseCode})
                </option>
              ))
            )}
          </select>
        </FormField>
        <div className="flex items-center justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            disabled={busy}
            className="rounded-xl border border-dm-border bg-dm-card px-4 py-2 text-sm font-medium text-dm-muted transition-colors hover:bg-dm-background hover:text-dm-foreground"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleAssign}
            disabled={busy || !subjectId}
            className={`${primaryButtonCompactClass} disabled:opacity-50`}
          >
            {busy && <Loader2 size={14} className="animate-spin" />}
            Assign
          </button>
        </div>
      </div>
    </Modal>
  )
}

function InstructorCard({
  instructor,
  subjects,
  expanded,
  onToggle,
  onEdit,
  onToggleStatus,
  onDelete,
  onAssign,
  onUnassign,
  unassigningId,
}) {
  const taught = subjects.filter((s) =>
    (s.instructorIds || []).includes(instructor.id),
  )
  return (
    <motion.div
      variants={fadeUp}
      layout
      className={`${adminCardClass} text-left transition-colors ${
        expanded ? 'ring-2 ring-dm-primary/30' : ''
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-amber-400/10 text-amber-400">
            <GraduationCap size={20} />
          </span>
          <div className="min-w-0">
            <h3 className="truncate text-base font-semibold text-dm-foreground">
              {instructor.name}
            </h3>
            <p className="flex items-center gap-1.5 text-xs text-dm-muted">
              <Mail size={11} />
              <span className="truncate">{instructor.email}</span>
            </p>
          </div>
        </div>
        <span
          className={`shrink-0 rounded-full px-2 py-0.5 text-[11px] font-medium capitalize ${statusBadge(
            instructor.status,
          )}`}
        >
          {instructor.status}
        </span>
      </div>

      <div className="mt-4 flex items-center justify-between text-sm text-dm-muted">
        <span className="flex items-center gap-1.5">
          <BookOpen size={14} className="text-dm-primary" />
          <span className="font-medium text-dm-foreground">{taught.length}</span>
          {taught.length === 1 ? 'subject' : 'subjects'}
        </span>
        <button
          type="button"
          onClick={onToggle}
          className="flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-medium text-dm-muted transition-colors hover:bg-dm-background hover:text-dm-foreground"
        >
          {expanded ? 'Hide' : 'Details'}
          <ChevronDown
            size={14}
            className={`transition-transform ${expanded ? 'rotate-180' : ''}`}
          />
        </button>
      </div>

      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="mt-3 overflow-hidden"
          >
            <div className="rounded-xl border border-dm-border/60 bg-dm-background/50 p-3">
              <div className="mb-2 flex items-center justify-between">
                <span className="text-[11px] font-medium uppercase tracking-wider text-dm-muted">
                  Subjects taught
                </span>
                <button
                  type="button"
                  onClick={onAssign}
                  className="flex items-center gap-1 rounded-lg bg-dm-primary/10 px-2 py-1 text-[11px] font-semibold text-dm-primary transition-colors hover:bg-dm-primary/20"
                >
                  <Plus size={12} />
                  Assign
                </button>
              </div>
              {taught.length === 0 ? (
                <p className="py-3 text-center text-xs text-dm-muted">
                  Not assigned to any subject yet.
                </p>
              ) : (
                <ul className="flex flex-col gap-1">
                  {taught.map((s) => (
                    <li
                      key={s.id}
                      className="flex items-center justify-between gap-2 rounded-lg bg-dm-card px-2.5 py-1.5"
                    >
                      <div className="min-w-0">
                        <p className="truncate text-sm text-dm-foreground">
                          {s.title}
                        </p>
                        <p className="truncate text-[11px] text-dm-muted">
                          {s.courseCode}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => onUnassign(s)}
                        disabled={unassigningId === s.id}
                        className="rounded-md p-1 text-dm-muted transition-colors hover:bg-red-400/10 hover:text-red-400 disabled:opacity-50"
                        title="Remove from subject"
                      >
                        {unassigningId === s.id ? (
                          <Loader2 size={12} className="animate-spin" />
                        ) : (
                          <X size={12} />
                        )}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={onEdit}
                className="rounded-lg border border-dm-border bg-dm-card px-2.5 py-1 text-xs font-medium text-dm-muted transition-colors hover:bg-dm-background hover:text-dm-foreground"
              >
                Edit profile
              </button>
              <button
                type="button"
                onClick={onToggleStatus}
                className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-colors ${
                  instructor.status === 'active'
                    ? 'bg-red-400/10 text-red-400 hover:bg-red-400/20'
                    : 'bg-emerald-400/10 text-emerald-400 hover:bg-emerald-400/20'
                }`}
              >
                {instructor.status === 'active' ? 'Disable' : 'Enable'}
              </button>
              <button
                type="button"
                onClick={onDelete}
                className="ml-auto rounded-lg px-2.5 py-1 text-xs font-medium text-red-400 transition-colors hover:bg-red-400/10"
              >
                Delete
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

function ManageInstructors() {
  const [instructors, setInstructors] = useState([])
  const [subjects, setSubjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [expandedId, setExpandedId] = useState(null)

  const [formOpen, setFormOpen] = useState(false)
  const [formMode, setFormMode] = useState('create')
  const [formUser, setFormUser] = useState(null)

  const [deleteTarget, setDeleteTarget] = useState(null)
  const [assignTarget, setAssignTarget] = useState(null)
  const [unassigningId, setUnassigningId] = useState(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const [uRes, sRes] = await Promise.all([
        getUsers({ role: 'instructor', pageSize: 1000 }),
        listSubjects({ pageSize: 1000 }),
      ])
      setInstructors(unwrapList(uRes).filter((u) => u.role === 'instructor'))
      setSubjects(unwrapList(sRes))
    } catch {
      toast.error('Could not load instructors.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return instructors
    return instructors.filter(
      (u) =>
        (u.name || '').toLowerCase().includes(q) ||
        (u.email || '').toLowerCase().includes(q) ||
        (u.username || '').toLowerCase().includes(q),
    )
  }, [instructors, search])

  const openCreate = () => {
    setFormMode('create')
    setFormUser(null)
    setFormOpen(true)
  }

  const openEdit = (u) => {
    setFormMode('edit')
    setFormUser(u)
    setFormOpen(true)
  }

  const handleToggleStatus = async (u) => {
    const next = u.status === 'active' ? 'disabled' : 'active'
    try {
      const updated = await setUserStatus(u.id, next)
      setInstructors((prev) =>
        prev.map((i) => (i.id === u.id ? { ...i, ...updated } : i)),
      )
      toast(`${u.name} ${next === 'active' ? 'enabled' : 'disabled'}`)
    } catch (err) {
      toast.error(
        err?.response?.data?.message || 'Could not update instructor.',
      )
    }
  }

  const handleUnassign = async (instructor, subject) => {
    setUnassigningId(subject.id)
    try {
      const next = (subject.instructorIds || []).filter(
        (id) => id !== instructor.id,
      )
      const updated = await updateSubject(subject.id, { instructorIds: next })
      setSubjects((prev) =>
        prev.map((s) => (s.id === subject.id ? { ...s, ...updated } : s)),
      )
      toast.success(`${instructor.name} removed from ${subject.title}`)
    } catch (err) {
      toast.error(
        err?.response?.data?.message || 'Could not update assignment.',
      )
    } finally {
      setUnassigningId(null)
    }
  }

  const confirmDelete = async () => {
    if (!deleteTarget) return
    try {
      await deleteUser(deleteTarget.id)
      toast.success(`${deleteTarget.name} deleted`)
      setInstructors((prev) => prev.filter((i) => i.id !== deleteTarget.id))
    } catch (err) {
      toast.error(
        err?.response?.data?.message || 'Could not delete instructor.',
      )
    } finally {
      setDeleteTarget(null)
    }
  }

  const availableForAssign = (instructor) =>
    subjects.filter(
      (s) => !(s.instructorIds || []).includes(instructor.id),
    )

  return (
    <AdminLayout title="Manage Instructors">
      <motion.div
        className="mx-auto max-w-7xl px-6 py-8 flex flex-col gap-6"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="relative w-full max-w-sm">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-dm-muted" />
            <input
              type="text"
              placeholder="Search instructors…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full rounded-xl border border-dm-border bg-dm-card py-2.5 pl-10 pr-4 text-sm text-dm-foreground placeholder:text-dm-muted focus:outline-none focus:ring-2 focus:ring-dm-primary/40"
            />
          </div>
          <button
            type="button"
            onClick={openCreate}
            className={`${primaryButtonCompactClass} px-3 py-2`}
          >
            <UserPlus size={14} />
            Add instructor
          </button>
        </div>

        {loading ? (
          <div className="py-12 text-center text-dm-muted">Loading instructors…</div>
        ) : filtered.length === 0 ? (
          <div className="py-12 text-center text-dm-muted">
            No instructors found.
          </div>
        ) : (
          <motion.div
            className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
            variants={stagger(0.05)}
            initial="hidden"
            animate="visible"
          >
            {filtered.map((u) => (
              <InstructorCard
                key={u.id}
                instructor={u}
                subjects={subjects}
                expanded={expandedId === u.id}
                onToggle={() =>
                  setExpandedId((prev) => (prev === u.id ? null : u.id))
                }
                onEdit={() => openEdit(u)}
                onToggleStatus={() => handleToggleStatus(u)}
                onDelete={() => setDeleteTarget(u)}
                onAssign={() => setAssignTarget(u)}
                onUnassign={(s) => handleUnassign(u, s)}
                unassigningId={unassigningId}
              />
            ))}
          </motion.div>
        )}
      </motion.div>

      <UserFormModal
        open={formOpen}
        onClose={() => setFormOpen(false)}
        mode={formMode}
        user={formUser}
        lockedRole="instructor"
        onSaved={refresh}
      />

      <ConfirmDialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={confirmDelete}
        title="Delete instructor"
        message={
          deleteTarget
            ? `Permanently delete ${deleteTarget.name}? They will be removed from all subject rosters.`
            : ''
        }
        confirmLabel="Delete"
        destructive
      />

      {assignTarget && (
        <AssignSubjectDialog
          open={!!assignTarget}
          onClose={() => setAssignTarget(null)}
          instructor={assignTarget}
          available={availableForAssign(assignTarget)}
          onAssigned={(updated) =>
            setSubjects((prev) =>
              prev.map((s) => (s.id === updated.id ? { ...s, ...updated } : s)),
            )
          }
        />
      )}
    </AdminLayout>
  )
}

export default ManageInstructors
