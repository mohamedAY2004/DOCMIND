import { Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import docmindLogo from '../../assets/docmind-logo.png'

const headerClass =
  'flex h-14 shrink-0 items-center justify-between border-b border-dm-border bg-dm-card px-4 md:px-6'
const backBtnClass =
  'flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-dm-muted hover:bg-dm-background hover:text-dm-foreground transition-colors'

function ChatHeader({ backTo, backLabel = 'Go back', rightSlot }) {
  return (
    <header className={headerClass}>
      <div className="flex items-center gap-2">
        {backTo && (
          <Link to={backTo} className={backBtnClass} aria-label={backLabel}>
            <ArrowLeft size={22} className="text-current" />
          </Link>
        )}
        <img
          src={docmindLogo}
          alt=""
          className="h-14 w-auto object-contain"
          aria-hidden
        />
        <span className="text-lg font-semibold text-dm-foreground">DocMind</span>
      </div>
      {rightSlot && <div className="flex items-center gap-2">{rightSlot}</div>}
    </header>
  )
}

export default ChatHeader
