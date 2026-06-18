import { useCallback, useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import {
  Search,
  ChevronDown,
  UserPlus,
  Pencil,
  KeyRound,
  Trash2,
  MoreVertical,
} from 'lucide-react'
import AdminLayout from '../../components/layout/AdminLayout'
import { primaryButtonCompactClass, primaryChipActiveClass } from '../../constants/themeClasses'
import Pagination from '../../components/ui/Pagination'
import UserFormModal from '../../components/admin/UserFormModal'
import ConfirmDialog from '../../components/admin/ConfirmDialog'
import {
  deleteUser,
  getUsers,
  resetUserPassword,
  setUserStatus,
} from '../../services/adminService'

const PAGE_SIZE = 8

const ROLE_OPTIONS = ['All', 'student', 'instructor', 'admin']

const thClass =
  'px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-dm-muted'
const tdClass = 'px-4 py-3.5 text-sm text-dm-foreground whitespace-nowrap'

function roleBadge(role) {
  const map = {
    student: 'bg-blue-400/10 text-blue-400',
    instructor: 'bg-amber-400/10 text-amber-400',
    admin: 'bg-dm-primary/10 text-dm-primary',
  }
  return map[role] || 'bg-dm-muted/10 text-dm-muted'
}

function statusBadge(status) {
  return status === 'active'
    ? 'bg-emerald-400/10 text-emerald-400'
    : 'bg-red-400/10 text-red-400'
}

function SortHeader({ label, field, sortKey, sortAsc, onSort }) {
  return (
    <th className={thClass}>
      <button
        type="button"
        onClick={() => onSort(field)}
        className="flex items-center gap-1 hover:text-dm-foreground transition-colors"
      >
        {label}
        {sortKey === field && (
          <ChevronDown
            size={14}
            className={`transition-transform ${sortAsc ? '' : 'rotate-180'}`}
          />
        )}
      </button>
    </th>
  )
}

function unwrapList(res) {
  if (!res) return []
  if (Array.isArray(res)) return res
  if (Array.isArray(res.items)) return res.items
  return []
}

function formatDate(value) {
  if (!value) return ''
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return String(value)
  return d.toISOString().slice(0, 10)
}

function ManageUsers() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState('All')
  const [sortKey, setSortKey] = useState('name')
  const [sortAsc, setSortAsc] = useState(true)
  const [page, setPage] = useState(1)
  const [menuOpenFor, setMenuOpenFor] = useState(null)

  const [formOpen, setFormOpen] = useState(false)
  const [formMode, setFormMode] = useState('create')
  const [formUser, setFormUser] = useState(null)

  const [deleteTarget, setDeleteTarget] = useState(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const res = await getUsers({ pageSize: 1000 })
      setUsers(unwrapList(res))
    } catch {
      toast.error('Could not load users.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  useEffect(() => {
    if (!menuOpenFor) return
    const onClick = () => setMenuOpenFor(null)
    window.addEventListener('click', onClick)
    return () => window.removeEventListener('click', onClick)
  }, [menuOpenFor])

  const handleSort = useCallback(
    (key) => {
      if (sortKey === key) {
        setSortAsc((prev) => !prev)
      } else {
        setSortKey(key)
        setSortAsc(true)
      }
      setPage(1)
    },
    [sortKey],
  )

  const filtered = useMemo(() => {
    let result = users
    if (roleFilter !== 'All') {
      result = result.filter((u) => u.role === roleFilter)
    }
    if (search.trim()) {
      const q = search.toLowerCase()
      result = result.filter(
        (u) =>
          (u.name || '').toLowerCase().includes(q) ||
          (u.email || '').toLowerCase().includes(q) ||
          (u.username || '').toLowerCase().includes(q) ||
          (u.id || '').toLowerCase().includes(q),
      )
    }
    result = [...result].sort((a, b) => {
      const aVal = a[sortKey] ?? ''
      const bVal = b[sortKey] ?? ''
      const cmp = String(aVal).localeCompare(String(bVal))
      return sortAsc ? cmp : -cmp
    })
    return result
  }, [users, search, roleFilter, sortKey, sortAsc])

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const paged = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  const toggleStatus = useCallback(async (id) => {
    const current = users.find((u) => u.id === id)
    if (!current) return
    const next = current.status === 'active' ? 'disabled' : 'active'

    setUsers((prev) =>
      prev.map((u) => (u.id === id ? { ...u, status: next } : u)),
    )

    try {
      const updated = await setUserStatus(id, next)
      setUsers((prev) =>
        prev.map((u) => (u.id === id ? { ...u, ...updated } : u)),
      )
      toast(next === 'active' ? `${current.name} enabled` : `${current.name} disabled`, {
        description: `Account is now ${next}`,
      })
    } catch (err) {
      setUsers((prev) =>
        prev.map((u) => (u.id === id ? current : u)),
      )
      const code = err?.response?.data?.code
      const msg =
        code === 'CANNOT_DISABLE_SELF'
          ? 'You cannot disable your own admin account.'
          : err?.response?.data?.message || 'Could not update user.'
      toast.error(msg)
    }
  }, [users])

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

  const handleSaved = async () => {
    await refresh()
  }

  const handleReset = async (u) => {
    try {
      const { temporaryPassword } = await resetUserPassword(u.id)
      try {
        if (navigator?.clipboard?.writeText) {
          await navigator.clipboard.writeText(temporaryPassword)
        }
      } catch {
        /* clipboard not available */
      }
      toast.success(`Temporary password for ${u.name}`, {
        description: `${temporaryPassword} (copied to clipboard)`,
        duration: 10000,
      })
    } catch (err) {
      toast.error(
        err?.response?.data?.message || 'Could not reset password.',
      )
    }
  }

  const confirmDelete = async () => {
    if (!deleteTarget) return
    try {
      await deleteUser(deleteTarget.id)
      toast.success(`${deleteTarget.name} deleted`)
      setUsers((prev) => prev.filter((u) => u.id !== deleteTarget.id))
    } catch (err) {
      const code = err?.response?.data?.code
      const msg =
        code === 'CANNOT_DELETE_SELF'
          ? 'You cannot delete your own account.'
          : err?.response?.data?.message || 'Could not delete user.'
      toast.error(msg)
    } finally {
      setDeleteTarget(null)
    }
  }

  return (
    <AdminLayout title="Manage Users">
      <motion.div
        className="mx-auto max-w-7xl px-6 py-8 flex flex-col gap-6"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        {/* Toolbar */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          {/* Search */}
          <div className="relative w-full max-w-sm">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-dm-muted" />
            <input
              type="text"
              placeholder="Search by name, email or username…"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1) }}
              className="w-full rounded-xl border border-dm-border bg-dm-card py-2.5 pl-10 pr-4 text-sm text-dm-foreground placeholder:text-dm-muted focus:outline-none focus:ring-2 focus:ring-dm-primary/40"
            />
          </div>
          <div className="flex items-center gap-2">
            {/* Role filter */}
            <div className="flex items-center gap-1">
              {ROLE_OPTIONS.map((r) => (
                <button
                  key={r}
                  type="button"
                  onClick={() => { setRoleFilter(r); setPage(1) }}
                  className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-all duration-200 ${
                    roleFilter === r
                      ? primaryChipActiveClass
                      : 'bg-dm-card border border-dm-border text-dm-muted hover:bg-dm-background hover:text-dm-foreground'
                  }`}
                >
                  {r === 'All' ? 'All' : r.charAt(0).toUpperCase() + r.slice(1)}
                </button>
              ))}
            </div>
            <button
              type="button"
              onClick={openCreate}
              className={`${primaryButtonCompactClass} px-3 py-2 text-xs`}
            >
              <UserPlus size={14} />
              Add user
            </button>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto rounded-2xl border border-dm-border bg-dm-card shadow-lg">
          <table className="w-full">
            <thead className="border-b border-dm-border">
              <tr>
                <th className={thClass}>ID</th>
                <SortHeader label="Name" field="name" sortKey={sortKey} sortAsc={sortAsc} onSort={handleSort} />
                <th className={thClass}>Email</th>
                <SortHeader label="Role" field="role" sortKey={sortKey} sortAsc={sortAsc} onSort={handleSort} />
                <th className={thClass}>Status</th>
                <SortHeader label="Registered" field="registeredAt" sortKey={sortKey} sortAsc={sortAsc} onSort={handleSort} />
                <SortHeader label="Last Active" field="lastActive" sortKey={sortKey} sortAsc={sortAsc} onSort={handleSort} />
                <th className={`${thClass} text-right`}>Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-dm-border/50">
              {loading ? (
                <tr>
                  <td colSpan={8} className="px-4 py-12 text-center text-dm-muted">
                    Loading users…
                  </td>
                </tr>
              ) : paged.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-12 text-center text-dm-muted">
                    No users found.
                  </td>
                </tr>
              ) : (
                paged.map((u) => (
                  <tr key={u.id} className="transition-colors hover:bg-dm-background/50">
                    <td className={`${tdClass} text-dm-muted font-mono text-xs`}>{u.id}</td>
                    <td className={`${tdClass} font-medium`}>{u.name}</td>
                    <td className={`${tdClass} text-dm-muted`}>{u.email}</td>
                    <td className={tdClass}>
                      <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${roleBadge(u.role)}`}>
                        {u.role}
                      </span>
                    </td>
                    <td className={tdClass}>
                      <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${statusBadge(u.status)}`}>
                        {u.status}
                      </span>
                    </td>
                    <td className={`${tdClass} text-dm-muted`}>{formatDate(u.registeredAt)}</td>
                    <td className={`${tdClass} text-dm-muted`}>{formatDate(u.lastActive)}</td>
                    <td className={`${tdClass} text-right`}>
                      <div className="inline-flex items-center gap-1.5">
                        <button
                          type="button"
                          onClick={() => toggleStatus(u.id)}
                          className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-all duration-200 ${
                            u.status === 'active'
                              ? 'bg-red-400/10 text-red-400 hover:bg-red-400/20'
                              : 'bg-emerald-400/10 text-emerald-400 hover:bg-emerald-400/20'
                          }`}
                        >
                          {u.status === 'active' ? 'Disable' : 'Enable'}
                        </button>
                        <div className="relative">
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation()
                              setMenuOpenFor((prev) => (prev === u.id ? null : u.id))
                            }}
                            className="rounded-lg border border-dm-border bg-dm-card p-1.5 text-dm-muted transition-colors hover:bg-dm-background hover:text-dm-foreground"
                          >
                            <MoreVertical size={14} />
                          </button>
                          {menuOpenFor === u.id && (
                            <div
                              onClick={(e) => e.stopPropagation()}
                              className="absolute right-0 top-full z-10 mt-1 w-44 overflow-hidden rounded-xl border border-dm-border bg-dm-card text-left text-sm shadow-xl"
                            >
                              <button
                                type="button"
                                onClick={() => { setMenuOpenFor(null); openEdit(u) }}
                                className="flex w-full items-center gap-2 px-3 py-2 text-dm-foreground hover:bg-dm-background"
                              >
                                <Pencil size={14} /> Edit
                              </button>
                              <button
                                type="button"
                                onClick={() => { setMenuOpenFor(null); handleReset(u) }}
                                className="flex w-full items-center gap-2 px-3 py-2 text-dm-foreground hover:bg-dm-background"
                              >
                                <KeyRound size={14} /> Reset password
                              </button>
                              <button
                                type="button"
                                onClick={() => { setMenuOpenFor(null); setDeleteTarget(u) }}
                                className="flex w-full items-center gap-2 px-3 py-2 text-red-400 hover:bg-red-400/10"
                              >
                                <Trash2 size={14} /> Delete
                              </button>
                            </div>
                          )}
                        </div>
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
          totalItems={filtered.length}
          pageSize={PAGE_SIZE}
          onPageChange={setPage}
        />
      </motion.div>

      <UserFormModal
        open={formOpen}
        onClose={() => setFormOpen(false)}
        mode={formMode}
        user={formUser}
        onSaved={handleSaved}
      />

      <ConfirmDialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={confirmDelete}
        title="Delete user"
        message={
          deleteTarget
            ? `Permanently delete ${deleteTarget.name} (${deleteTarget.email})? This cannot be undone.`
            : ''
        }
        confirmLabel="Delete"
        destructive
      />
    </AdminLayout>
  )
}

export default ManageUsers
