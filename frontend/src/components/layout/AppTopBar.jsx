import { Link } from 'react-router-dom'
import { ArrowLeft, Menu } from 'lucide-react'
import DocMindLogo from '../ui/DocMindLogo'

const barClass = 'flex h-14 items-center gap-3 px-4 md:px-6'
const logoClass = 'h-8 w-auto object-contain'
const menuButtonClass =
  'flex h-10 w-10 items-center justify-center rounded-lg text-dm-muted hover:bg-dm-background lg:hidden'
const backButtonClass =
  'flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-dm-muted hover:bg-dm-background hover:text-dm-foreground transition-colors'

function AppTopBar({ title, showLogo = false, logoClassName, logoHref, backTo, onMenuClick, children }) {
  const logoContent = (
    <>
      {showLogo && (
        <DocMindLogo className={logoClassName || logoClass} alt="" />
      )}
      {title && <span className="text-lg font-semibold text-dm-foreground">{title}</span>}
    </>
  )

  return (
    <div className={barClass}>
      {backTo && (
        <Link to={backTo} className={backButtonClass} aria-label="Go back">
          <ArrowLeft size={22} className="text-current" />
        </Link>
      )}
      {onMenuClick && (
        <button
          type="button"
          onClick={onMenuClick}
          className={menuButtonClass}
          aria-label="Open menu"
        >
          <Menu size={24} className="text-current" />
        </button>
      )}
      {logoHref ? (
        <Link to={logoHref} className="flex items-center gap-3 transition-opacity hover:opacity-80">
          {logoContent}
        </Link>
      ) : (
        <div className="flex items-center gap-3">{logoContent}</div>
      )}
      {children}
    </div>
  )
}

export default AppTopBar
