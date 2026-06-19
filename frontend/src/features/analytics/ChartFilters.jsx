import { BookOpen, GraduationCap, Layers, X } from 'lucide-react'
import InlineSelect from './InlineSelect'

/**
 * Renders the shared semester / instructor / (optional) subject selects plus a
 * clear button for a single diagram. Driven by a `useSubjectFilters` instance.
 */
function ChartFilters({ filters, semesters, showSubject = false }) {
  return (
    <>
      <InlineSelect
        icon={Layers}
        ariaLabel="Filter by semester"
        value={filters.semester}
        onChange={(e) => filters.setSemester(e.target.value)}
      >
        <option value="all">All semesters</option>
        {semesters.map((s) => (
          <option key={s.id} value={s.id}>{s.label}</option>
        ))}
      </InlineSelect>

      <InlineSelect
        icon={GraduationCap}
        ariaLabel="Filter by instructor"
        value={filters.instructor}
        onChange={(e) => filters.setInstructor(e.target.value)}
      >
        <option value="all">All instructors</option>
        {filters.instructorOptions.map((i) => (
          <option key={i.id} value={i.id}>{i.name}</option>
        ))}
      </InlineSelect>

      {showSubject ? (
        <InlineSelect
          icon={BookOpen}
          ariaLabel="Filter by subject"
          value={filters.subject}
          onChange={(e) => filters.setSubject(e.target.value)}
        >
          <option value="all">All subjects</option>
          {filters.subjectOptions.map((s) => (
            <option key={s.id} value={s.id}>{s.title}</option>
          ))}
        </InlineSelect>
      ) : null}

      {filters.isActive ? (
        <button
          type="button"
          onClick={filters.reset}
          className="flex items-center gap-1 rounded-lg px-2 py-1.5 text-xs font-medium text-red-400 transition-colors hover:bg-red-400/10"
        >
          <X size={13} />
          Clear
        </button>
      ) : null}
    </>
  )
}

export default ChartFilters
