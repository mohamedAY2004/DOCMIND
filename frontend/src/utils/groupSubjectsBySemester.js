/**
 * Group a flat list of subjects into per-semester sections.
 *
 * Subjects carry only `semesterId` + `semesterState`; the semesters list (from
 * GET /semesters, already ordered newest-first) supplies human labels and the
 * section order. Subjects with no semester — or a semesterId not present in the
 * semesters list — fall into a trailing "Other" group.
 *
 * @param {Array<{id:string, semesterId?:string|null, semesterState?:string}>} subjects
 * @param {Array<{id:string, label:string, state?:string}>} semesters
 * @returns {Array<{ semester: {id:string, label:string, state:string} | null, subjects: Array }>}
 *          ordered for display (known semesters newest-first, then "Other").
 */
export function groupSubjectsBySemester(subjects = [], semesters = []) {
  const knownOrder = []
  const byId = new Map()
  for (const sem of semesters) {
    if (!sem || sem.id == null) continue
    if (!byId.has(sem.id)) {
      byId.set(sem.id, {
        id: sem.id,
        label: sem.label || sem.id,
        state: sem.state || 'active',
      })
      knownOrder.push(sem.id)
    }
  }

  // Bucket subjects; remember the order unknown semesterIds first appear so the
  // soft-degrade path (no /semesters data) still renders a stable order.
  const buckets = new Map() // semesterId -> subjects[]
  const unknownOrder = []
  let other = null // collects null / unmatched-semesterId subjects

  for (const subject of subjects) {
    const sid = subject?.semesterId
    if (sid != null && byId.has(sid)) {
      if (!buckets.has(sid)) buckets.set(sid, [])
      buckets.get(sid).push(subject)
    } else if (sid != null) {
      // Unknown-but-present semesterId: keep its own section using the id as a
      // fallback label so nothing silently collapses into "Other".
      if (!buckets.has(sid)) {
        buckets.set(sid, [])
        unknownOrder.push(sid)
        byId.set(sid, { id: sid, label: sid, state: subject?.semesterState || 'active' })
      }
      buckets.get(sid).push(subject)
    } else {
      if (!other) other = []
      other.push(subject)
    }
  }

  const groups = []
  for (const sid of [...knownOrder, ...unknownOrder]) {
    const items = buckets.get(sid)
    if (items && items.length) groups.push({ semester: byId.get(sid), subjects: items })
  }
  if (other && other.length) groups.push({ semester: null, subjects: other })
  return groups
}

export default groupSubjectsBySemester
