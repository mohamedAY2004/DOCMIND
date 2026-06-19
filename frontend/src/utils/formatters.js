export function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

/** Server-generated user id: ``U`` + 12 uppercase hex chars (see backend ``_new_user_id``). */
const OPAQUE_USER_ID_RE = /^U[0-9A-F]{12}$/

function formatLocalEmailPart(email) {
  if (!email || typeof email !== 'string') return ''
  const local = email.split('@')[0]
  if (!local) return ''
  return local.replace(/[._]+/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

/** Turn ``bob_prof`` / ``alice.m`` into a short display label. */
function formatUsernameForDisplay(username) {
  if (!username || typeof username !== 'string') return ''
  const s = username.trim()
  if (!s) return ''
  return s.replace(/[._]+/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

/**
 * Human-readable label for roster UIs when ``name`` is missing or mistakenly
 * equals the opaque id (legacy / bad data).
 */
export function instructorDisplayName({ id, name, email, username } = {}) {
  const n = typeof name === 'string' ? name.trim() : ''
  if (n && !OPAQUE_USER_ID_RE.test(n)) return n
  const fromEmail = formatLocalEmailPart(email)
  if (fromEmail) return fromEmail
  const fromUsername = formatUsernameForDisplay(username)
  if (fromUsername) return fromUsername
  if (id && typeof id === 'string' && OPAQUE_USER_ID_RE.test(id)) {
    return `Instructor (${id.slice(-4)})`
  }
  return n || id || 'Instructor'
}

/** Map one roster element from GET /subjects/:id/instructors (shape-tolerant). */
export function normalizeInstructorRow(raw) {
  if (!raw || typeof raw !== 'object') return null
  const id = raw.id ?? raw.userId ?? raw.user_id
  if (!id) return null
  const email = typeof raw.email === 'string' ? raw.email : ''
  const username = typeof raw.username === 'string' ? raw.username : ''
  const name = instructorDisplayName({
    id,
    name: raw.name,
    email,
    username,
  })
  const instructorRole =
    raw.instructorRole ?? raw.instructor_role ?? 'viewer'
  return { id, name, email, username, instructorRole }
}

/** Build a two-letter initials label for an instructor display name. */
export function getInstructorInitials(name) {
  if (!name) return '??'
  const parts = name.replace(/^Dr\.?\s+/i, '').trim().split(/\s+/)
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

/**
 * Title-case fallback for a subject slug when no server value is available
 * (e.g. transient route navigation before a fetch completes).
 */
export function titleCaseSlug(slug) {
  if (!slug) return ''
  return slug.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}
