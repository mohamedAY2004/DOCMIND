import { useCallback, useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import {
  Search,
  BookPlus,
  Pencil,
  Trash2,
  Users,
  GraduationCap,
  FileText,
  MoreVertical,
} from 'lucide-react'
import AdminLayout from '../../components/layout/AdminLayout'
import { primaryButtonCompactClass, primaryChipActiveClass } from '../../constants/themeClasses'
import Pagination from '../../components/ui/Pagination'
import SubjectFormModal from '../../components/admin/SubjectFormModal'
import ConfirmDialog from '../../components/admin/ConfirmDialog'
import {
  deleteSubject,
  getSemesters,
  getUsers,
  listSubjects,
} from '../../services/adminService'

const PAGE_SIZE = 10

const thClass =
  'px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-dm-muted'
const tdClass = 'px-4 py-3.5 text-sm text-dm-foreground align-top'

function unwrapList(res) {
  if (!res) return []
  if (Array.isArray(res)) return res
  if (Array.isArray(res.items)) return res.items
  return []
}

function ManageSubjects() {
  const [subjects, setSubjects] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)

  const [semesters, setSemesters] = useState([])
  const [instructorsById, setInstructorsById] = useState({})

  const [search, setSearch] = useState('')
  const [searchDraft, setSearchDraft] = useState('')
  const [semesterFilter, setSemesterFilter] = useState('all')
  const [page, setPage] = useState(1)

  const [formOpen, setFormOpen] = useState(false)
  const [formMode, setFormMode] = useState('create')
  const [formSubject, setFormSubject] = useState(null)

  const [deleteTarget, setDeleteTarget] = useState(null)
  const [menuOpenFor, setMenuOpenFor] = useState(null)

  const loadAuxData = useCallback(async () => {
    try {
      const [semRes, insRes] = await Promise.all([
        getSemesters().catch(() => []),
        getUsers({ role: 'instructor', pageSize: 1000 }).catch(() => null),
      ])
      setSemesters(unwrapList(semRes))
      const map = {}
      unwrapList(insRes)
        .filter((u) => u.role === 'instructor')
        .forEach((i) => {
          map[i.id] = i
        })
      setInstructorsById(map)
    } catch {
      /* non-fatal */
    }
  }, [])

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const params = { page, pageSize: PAGE_SIZE }
      if (search.trim()) params.search = search.trim()
      if (semesterFilter !== 'all') params.semesterId = semesterFilter
      const res = await listSubjects(params)
      setSubjects(unwrapList(res))
      setTotal(res?.total ?? unwrapList(res).length)
    } catch {
      toast.error('Could not load subjects.')
    } finally {
      setLoading(false)
    }
  }, [page, search, semesterFilter])

  useEffect(() => {
    loadAuxData()
  }, [loadAuxData])

  useEffect(() => {
    refresh()
  }, [refresh])

  useEffect(() => {
    if (!menuOpenFor) return
    const onClick = () => setMenuOpenFor(null)
    window.addEventListener('click', onClick)
    return () => window.removeEventListener('click', onClick)
  }, [menuOpenFor])

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  const semesterLabel = useMemo(() => {
    const map = {}
    semesters.forEach((s) => {
      map[s.id] = s.label
    })
    return map
  }, [semesters])

  const openCreate = () => {
    setFormMode('create')
    setFormSubject(null)
    setFormOpen(true)
  }

  const openEdit = (subject) => {
    setFormMode('edit')
    setFormSubject(subject)
    setFormOpen(true)
  }

  const confirmDelete = async () => {
    if (!deleteTarget) return
    try {
      await deleteSubject(deleteTarget.id)
      toast.success(`${deleteTarget.title} deleted`)
      refresh()
    } catch (err) {
      const code = err?.response?.data?.code
      const msg =
        code === 'CONFLICT'
          ? 'This subject has active conversations and cannot be deleted.'
          : err?.response?.data?.message || 'Could not delete subject.'
      toast.error(msg)
    } finally {
      setDeleteTarget(null)
    }
  }

  const handleSubmitSearch = (e) => {
    e.preventDefault()
    setPage(1)
    setSearch(searchDraft)
  }

  return (
    <AdminLayout title="Manage Subjects">
      <motion.div
        className="mx-auto max-w-7xl px-6 py-8 flex flex-col gap-6"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        {/* Toolbar */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <form
            onSubmit={handleSubmitSearch}
            className="relative w-full max-w-sm"
          >
            <Search
              size={16}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-dm-muted"
            />
            <input
              type="text"
              placeholder="Search by title, course code or id…"
              value={searchDraft}
              onChange={(e) => setSearchDraft(e.target.value)}
              className="w-full rounded-xl border border-dm-border bg-dm-card py-2.5 pl-10 pr-4 text-sm text-dm-foreground placeholder:text-dm-muted focus:outline-none focus:ring-2 focus:ring-dm-primary/40"
            />
          </form>

          <div className="flex items-center gap-2">
            <select
              value={semesterFilter}
              onChange={(e) => {
                setSemesterFilter(e.target.value)
                setPage(1)
              }}
              className="rounded-xl border border-dm-border bg-dm-card py-2 pl-3 pr-8 text-sm text-dm-foreground focus:outline-none focus:ring-2 focus:ring-dm-primary/40"
            >
              <option value="all">All semesters</option>
              {semesters.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.label}
                </option>
              ))}
            </select>
            <button
              type="button"
              onClick={openCreate}
              className={`${primaryButtonCompactClass} px-3 py-2`}
            >
              <BookPlus size={14} />
              Add subject
            </button>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto rounded-2xl border border-dm-border bg-dm-card shadow-lg">
          <table className="w-full">
            <thead className="border-b border-dm-border">
              <tr>
                <th className={thClass}>ID</th>
                <th className={thClass}>Title</th>
                <th className={thClass}>Course</th>
                <th className={thClass}>Semester</th>
                <th className={thClass}>Instructors</th>
                <th className={thClass}>Students</th>
                <th className={thClass}>PDFs</th>
                <th className={`${thClass} text-right`}>Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-dm-border/50">
              {loading ? (
                <tr>
                  <td
                    colSpan={8}
                    className="px-4 py-12 text-center text-dm-muted"
                  >
                    Loading subjects…
                  </td>
                </tr>
              ) : subjects.length === 0 ? (
                <tr>
                  <td
                    colSpan={8}
                    className="px-4 py-12 text-center text-dm-muted"
                  >
                    No subjects found.
                  </td>
                </tr>
              ) : (
                subjects.map((s) => (
                  <tr
                    key={s.id}
                    className="transition-colors hover:bg-dm-background/50"
                  >
                    <td
                      className={`${tdClass} text-dm-muted font-mono text-xs`}
                    >
                      {s.id}
                    </td>
                    <td className={`${tdClass} font-medium`}>
                      <p className="text-dm-foreground">{s.title}</p>
                      <p className="mt-0.5 line-clamp-1 text-xs text-dm-muted">
                        {s.description}
                      </p>
                    </td>
                    <td className={`${tdClass} text-dm-muted`}>
                      {s.courseCode}
                    </td>
                    <td className={`${tdClass} text-dm-muted`}>
                      {semesterLabel[s.semesterId || s.semester] || '—'}
                    </td>
                    <td className={tdClass}>
                      <div className="flex flex-wrap gap-1">
                        {(s.instructorIds || []).length === 0 ? (
                          <span className="text-xs text-dm-muted">
                            Unassigned
                          </span>
                        ) : (
                          (s.instructorIds || []).map((id) => {
                            const ins = instructorsById[id]
                            const isSuper = id === s.superInstructorId
                            return (
                              <span
                                key={id}
                                className={[
                                  'flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium',
                                  isSuper
                                    ? 'bg-dm-primary/15 text-dm-primary'
                                    : 'bg-amber-400/10 text-amber-400',
                                ].join(' ')}
                                title={isSuper ? 'Super instructor' : 'Viewer instructor'}
                              >
                                <GraduationCap size={10} />
                                {ins?.name || id}
                                {isSuper && (
                                  <span className="ml-0.5 text-[10px]">★</span>
                                )}
                              </span>
                            )
                          })
                        )}
                      </div>
                    </td>
                    <td className={`${tdClass} text-dm-muted`}>
                      <span className="inline-flex items-center gap-1">
                        <Users size={12} />
                        {s.studentCount ?? (s.studentIds || []).length}
                      </span>
                    </td>
                    <td className={`${tdClass} text-dm-muted`}>
                      <span className="inline-flex items-center gap-1">
                        <FileText size={12} />
                        {s.pdfCount}
                      </span>
                    </td>
                    <td className={`${tdClass} text-right`}>
                      <div className="relative inline-block">
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
                            onClick={(e) => {
                              e.stopPropagation()
                              setMenuOpenFor((prev) =>
                                prev === s.id ? null : s.id,
                              )
                            }}
                            className="rounded-lg border border-dm-border bg-dm-card p-1.5 text-dm-muted transition-colors hover:bg-dm-background hover:text-dm-foreground"
                          >
                            <MoreVertical size={14} />
                          </button>
                        </div>
                        {menuOpenFor === s.id && (
                          <div
                            onClick={(e) => e.stopPropagation()}
                            className="absolute right-0 top-full z-10 mt-1 w-40 overflow-hidden rounded-xl border border-dm-border bg-dm-card text-left text-sm shadow-xl"
                          >
                            <button
                              type="button"
                              onClick={() => {
                                setMenuOpenFor(null)
                                setDeleteTarget(s)
                              }}
                              className="flex w-full items-center gap-2 px-3 py-2 text-red-400 hover:bg-red-400/10"
                            >
                              <Trash2 size={14} /> Delete
                            </button>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <Pagination
          page={page}
          totalPages={totalPages}
          totalItems={total}
          pageSize={PAGE_SIZE}
          onPageChange={setPage}
        />
      </motion.div>

      <SubjectFormModal
        open={formOpen}
        onClose={() => setFormOpen(false)}
        mode={formMode}
        subject={formSubject}
        onSaved={refresh}
      />

      <ConfirmDialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={confirmDelete}
        title="Delete subject"
        message={
          deleteTarget
            ? `Delete ${deleteTarget.title}? Materials and rosters will also be removed. This cannot be undone.`
            : ''
        }
        confirmLabel="Delete"
        destructive
      />
    </AdminLayout>
  )
}

export default ManageSubjects
