import { FileUp } from 'lucide-react'
import PrimaryButton from './PrimaryButton'

const zoneClass =
  'flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-dm-border bg-dm-background/50 py-10 px-6 text-center'
const iconWrapClass = 'flex justify-center text-dm-primary'
const titleClass = 'mt-3 font-medium text-dm-foreground'
const hintClass = 'mt-1 text-sm text-dm-muted'
const buttonWrapClass = 'mt-5'

function UploadZone({
  title = 'Click or drag files to upload',
  hint = 'Upload lecture slides, notes, or reference books to train the bot.',
  buttonText = 'Browse Files',
  onBrowse,
  className = '',
}) {
  return (
    <div className={[zoneClass, className].filter(Boolean).join(' ')}>
      <div className={iconWrapClass}>
        <FileUp size={40} strokeWidth={1.5} />
      </div>
      <p className={titleClass}>{title}</p>
      <p className={hintClass}>{hint}</p>
      <div className={buttonWrapClass}>
        <PrimaryButton type="button" onClick={onBrowse}>
          {buttonText}
        </PrimaryButton>
      </div>
    </div>
  )
}

export default UploadZone
