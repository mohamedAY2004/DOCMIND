import { useCallback, useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import { CalendarPlus, Pencil, Trash2 } from 'lucide-react'
import AdminLayout from '../../components/layout/AdminLayout'
import { primaryButtonCompactClass } from '../../constants/themeClasses'
import SemesterFormModal from '../../components/admin/SemesterFormModal'
import ConfirmDialog from '../../components/admin/ConfirmDialog'
import { deleteSemester, getSemesters } from '../../services/adminService'

const thClass =
  'px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-dm-muted'
const tdClass = 'px-4 py-3.5 text-sm text-dm-foreground align-middle'

// Visual treatment per derived lifecycle state (matches the student SubjectCard).
const STATE_BADGE = {
  active: { label: 'Active', cls: 'bg-emerald-500/15 text-emerald-400 ring-emerald-500/30' },
  archived: { label: 'Archived', cls: 'bg-amber-500/15 text-amber-400 ring-amber-500/30' },
  upcoming: { label: 'Upcoming', cls: 'bg-sky-500/15 text-sky-400 ring-sky-500/30' },
}

function unwrapList(res) {
  if (!res) return []
  if (Array.isArray(res)) return res
  if (Array.isArray(res.items)) return res.items
  return []
}

function fmtDate(iso) {
  if (!iso) return '—'
  const d = new Date(`${iso}T00:00:00`)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

function StateBadge({ state }) {
  const badge = STATE_BADGE[state] || STATE_BADGE.active
  return (
    <span
      className={`rounded-full px-2.5 py-0.5 text-[11px] font-semibold ring-1 ${badge.cls}`}
    >
      {badge.label}
    </span>
  )
}

function ManageSemesters() {
  const [semesters, setSemesters] = useState([])
  const [loading, setLoading] = useState(true)

  const [formOpen, setFormOpen] = useState(false)
  const [formMode, setFormMode] = useState('create')
  const [formSemester, setFormSemester] = useState(null)

  const [deleteTarget, setDeleteTarget] = useState(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const res = await getSemesters()
      setSemesters(unwrapList(res))
    } catch {
      toast.error('Could not load semesters.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const openCreate = () => {
    setFormMode('create')
    setFormSemester(null)
    setFormOpen(true)
  }

  const openEdit = (semester) => {
    setFormMode('edit')
    setFormSemester(semester)
    setFormOpen(true)
  }

  const confirmDelete = async () => {
    if (!deleteTarget) return
    try {
      await deleteSemester(deleteTarget.id)
      toast.success(`${deleteTarget.label} deleted`)
      refresh()
    } catch (err) {
      toast.error(err?.response?.data?.message || 'Could not delete semester.')
    } finally {
      setDeleteTarget(null)
    }
  }

  return (
    <AdminLayout title="Manage Semesters">
      <motion.div
        className="mx-auto max-w-5xl px-6 py-8 flex flex-col gap-6"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <div className="flex items-center justify-between gap-3">
          <p className="text-sm text-dm-muted">
            Terms group subjects and drive the read-only state of past semesters.
          </p>
          <button
            type="button"
            onClick={openCreate}
            className={`${primaryButtonCompactClass} px-3 py-2`}
          >
            <CalendarPlus size={14} />
            Add semester
          </button>
        </div>

        <div className="overflow-x-auto rounded-2xl border border-dm-border bg-dm-card shadow-lg">
          <table className="w-full">
            <thead className="border-b border-dm-border">
              <tr>
                <th className={thClass}>Label</th>
                <th className={thClass}>ID</th>
                <th className={thClass}>Start</th>
                <th className={thClass}>End</th>
                <th className={thClass}>State</th>
                <th className={`${thClass} text-right`}>Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-dm-border/50">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-dm-muted">
                    Loading semesters…
                  </td>
                </tr>
              ) : semesters.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-dm-muted">
                    No semesters yet. Add one to get started.
                  </td>
                </tr>
              ) : (
                semesters.map((s) => (
                  <tr key={s.id} className="transition-colors hover:bg-dm-background/50">
                    <td className={`${tdClass} font-medium`}>
                      <span className="inline-flex items-center gap-2">
                        {s.label}
                        {s.isCurrent && (
                          <span className="rounded-full bg-dm-primary/15 px-2 py-0.5 text-[10px] font-semibold text-dm-primary">
                            Current
                          </span>
                        )}
                      </span>
                    </td>
                    <td className={`${tdClass} font-mono text-xs text-dm-muted`}>{s.id}</td>
                    <td className={`${tdClass} text-dm-muted`}>{fmtDate(s.startDate)}</td>
                    <td className={`${tdClass} text-dm-muted`}>{fmtDate(s.endDate)}</td>
                    <td className={tdClass}>
                      <StateBadge state={s.state} />
                    </td>
                    <td className={`${tdClass} text-right`}>
                      <div className="inline-flex items-center gap-1.5">
                        <button
                          type="button"
                          onClick={() => openEdit(s)}
                          className="rounded-lg border border-dm-border bg-dm-card px-2.5 py-1 text-xs font-medium text-dm-muted transition-colors hover:bg-dm-background hover:text-dm-foreground"
                        >
                          <Pencil size={12} className="inline" /> Edit
                        </button>
                        <button
                          type="button"
                          onClick={() => setDeleteTarget(s)}
                          className="rounded-lg border border-dm-border bg-dm-card p-1.5 text-red-400 transition-colors hover:bg-red-400/10"
                          aria-label={`Delete ${s.label}`}
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </motion.div>

      <SemesterFormModal
        open={formOpen}
        onClose={() => setFormOpen(false)}
        mode={formMode}
        semester={formSemester}
        onSaved={refresh}
      />

      <ConfirmDialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={confirmDelete}
        title="Delete semester"
        message={
          deleteTarget
            ? `Delete ${deleteTarget.label}? Subjects in this term will become unassigned (and revert to always-active). This cannot be undone.`
            : ''
        }
        confirmLabel="Delete"
        destructive
      />
    </AdminLayout>
  )
}

export default ManageSemesters
