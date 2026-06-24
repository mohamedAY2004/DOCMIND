import { Link } from 'react-router-dom'
import { FileText, Loader2, ShieldCheck, Eye, Archive } from 'lucide-react'
import PrimaryButton from './PrimaryButton'
import { primarySurfaceClass } from '../../constants/themeClasses'

const cardClass =
  'flex flex-col overflow-hidden rounded-card border border-dm-border bg-dm-card shadow-xl transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl hover:border-dm-primary/40'
const imageWrapClass =
  'relative h-36 w-full bg-dm-background'
const imagePlaceholderClass =
  'flex h-full w-full items-center justify-center text-dm-muted/50'
const statusBadgeReadyClass =
  'absolute right-3 top-3 flex items-center gap-1.5 rounded-full bg-dm-statusProcessed/90 px-2.5 py-1 text-xs font-medium text-dm-foreground'
const statusBadgeProcessingClass =
  'absolute right-3 top-3 flex items-center gap-1.5 rounded-full bg-dm-statusIndexing/90 px-2.5 py-1 text-xs font-medium text-dm-foreground'
const statusBadgeArchivedClass =
  'absolute right-3 top-3 flex items-center gap-1.5 rounded-full bg-amber-500/15 px-2.5 py-1 text-xs font-medium text-amber-400 ring-1 ring-inset ring-amber-500/30'
const bodyClass = 'flex flex-col p-5'
const titleClass = 'text-lg font-bold text-dm-foreground'
const courseInfoClass = 'mt-1 text-sm text-dm-muted'
const pdfRowClass = 'mt-3 flex items-center gap-2 text-sm text-dm-muted'
const buttonWrapClass = 'mt-5'
const buttonLinkClass =
  `${primarySurfaceClass} block w-full rounded-xl py-3 px-4 text-center font-medium transition-opacity hover:opacity-95`

function StatusBadge({ status }) {
  if (status === 'archived') {
    return (
      <span className={statusBadgeArchivedClass}>
        <Archive size={12} className="shrink-0" aria-hidden />
        Bot offline
      </span>
    )
  }
  if (status === 'ready') {
    return (
      <span className={statusBadgeReadyClass}>
        <span className="h-2 w-2 rounded-full bg-dm-statusProcessed" aria-hidden />
        Bot ready
      </span>
    )
  }
  if (status === 'processing' || status === 'uploading') {
    return (
      <span className={statusBadgeProcessingClass}>
        <Loader2 size={12} className="shrink-0 animate-spin" aria-hidden />
        Processing
      </span>
    )
  }
  return null
}

function InstructorSubjectCard({
  title,
  courseCode,
  pdfCount,
  status = 'ready',
  image,
  href,
  className = '',
  instructorRole = null,
  isArchived = false,
}) {
  const isUploading = status === 'uploading'
  const isSuper = instructorRole === 'super'
  // Archived subjects are read-only — even a super instructor can only view
  // and download, so the CTA reflects that.
  const buttonLabel = isArchived || !isSuper ? 'View Subject' : 'Manage Subject'

  const content = (
    <>
      <div className={imageWrapClass}>
        {image ? (
          <img src={image} alt="" className="h-full w-full object-cover" />
        ) : (
          <div className={imagePlaceholderClass}>
            <FileText size={40} className="opacity-50" />
          </div>
        )}
        <StatusBadge status={status} />
      </div>
      <div className={bodyClass}>
        <h3 className={titleClass}>{title}</h3>
        <p className={courseInfoClass}>{courseCode}</p>
        <div className={pdfRowClass}>
          <FileText size={16} className="shrink-0 text-dm-muted" />
          {isUploading ? (
            <span>Uploading...</span>
          ) : (
            <span>{pdfCount}</span>
          )}
        </div>
        {instructorRole && (
          <div className="mt-3">
            {isSuper ? (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-dm-primary/15 px-2.5 py-1 text-xs font-medium text-dm-primary">
                <ShieldCheck size={12} />
                Super Instructor
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-dm-background border border-dm-border px-2.5 py-1 text-xs font-medium text-dm-muted">
                <Eye size={12} />
                Viewer
              </span>
            )}
          </div>
        )}
        <div className={buttonWrapClass}>
          {href ? (
            <Link to={href} className={buttonLinkClass}>
              {buttonLabel}
            </Link>
          ) : (
            <PrimaryButton fullWidth={false} className="w-full">
              {buttonLabel}
            </PrimaryButton>
          )}
        </div>
      </div>
    </>
  )

  return <div className={[cardClass, className].filter(Boolean).join(' ')}>{content}</div>
}

export default InstructorSubjectCard
