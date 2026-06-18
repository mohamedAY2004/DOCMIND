import { ChevronLeft, ChevronRight } from 'lucide-react'
import { primaryChipActiveClass } from '../../constants/themeClasses'

const navBtnClass =
  'rounded-lg p-1.5 hover:bg-dm-background transition-colors disabled:opacity-30 disabled:pointer-events-none'

function Pagination({ page, totalPages, totalItems, pageSize, onPageChange }) {
  const start = Math.min((page - 1) * pageSize + 1, totalItems)
  const end = Math.min(page * pageSize, totalItems)

  return (
    <div className="flex items-center justify-between text-sm text-dm-muted">
      <span>
        Showing {start}–{end} of {totalItems}
      </span>
      <div className="flex items-center gap-1">
        <button
          type="button"
          onClick={() => onPageChange(Math.max(1, page - 1))}
          disabled={page === 1}
          className={navBtnClass}
        >
          <ChevronLeft size={18} />
        </button>
        {Array.from({ length: totalPages }, (_, i) => i + 1).map((n) => (
          <button
            key={n}
            type="button"
            onClick={() => onPageChange(n)}
            className={`h-8 w-8 rounded-lg text-xs font-medium transition-all duration-200 ${
              page === n
                ? primaryChipActiveClass
                : 'hover:bg-dm-background text-dm-muted'
            }`}
          >
            {n}
          </button>
        ))}
        <button
          type="button"
          onClick={() => onPageChange(Math.min(totalPages, page + 1))}
          disabled={page === totalPages}
          className={navBtnClass}
        >
          <ChevronRight size={18} />
        </button>
      </div>
    </div>
  )
}

export default Pagination
