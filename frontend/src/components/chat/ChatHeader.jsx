import AppTopBar from '../layout/AppTopBar'
import ThemeToggle from '../ui/ThemeToggle'

const headerClass =
  'shrink-0 border-b border-dm-border bg-dm-card'

function ChatHeader({ backTo, backLabel = 'Go back', rightSlot }) {
  return (
    <header className={headerClass}>
      <AppTopBar
        title="DocMind"
        showLogo
        logoClassName="h-14 w-auto object-contain"
        backTo={backTo}
      >
        <div className="ml-auto flex items-center gap-2">
          <ThemeToggle />
          {rightSlot}
        </div>
      </AppTopBar>
    </header>
  )
}

export default ChatHeader
