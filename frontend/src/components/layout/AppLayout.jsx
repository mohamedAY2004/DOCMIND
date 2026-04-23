import { useState } from 'react'

const FIXED_ROOT = 'h-screen flex flex-col bg-dm-background overflow-hidden'
const SCROLLABLE_ROOT = 'min-h-screen flex flex-col bg-dm-background'

const topNavClass = 'sticky top-0 z-30 shrink-0 border-b border-dm-border bg-dm-card'
const sidebarClass = 'hidden lg:flex lg:w-64 lg:shrink-0 lg:flex-col lg:border-r lg:border-dm-border lg:bg-dm-card'
const mainClass = 'flex-1 min-w-0 flex flex-col'
const mobileSidebarBackdropClass = 'fixed inset-0 z-40 bg-black/50 lg:hidden'
const mobileSidebarPanelClass = 'fixed inset-y-0 left-0 z-50 w-64 flex flex-col bg-dm-card border-r border-dm-border lg:hidden'

function AppLayout({ sidebar, topNav, scrollable = false, children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const openSidebar = () => setSidebarOpen(true)
  const closeSidebar = () => setSidebarOpen(false)

  const rootClass = scrollable ? SCROLLABLE_ROOT : FIXED_ROOT
  const bodyClass = scrollable ? 'flex flex-1' : 'flex flex-1 min-h-0'
  const contentClass = scrollable
    ? 'flex-1 flex flex-col'
    : 'flex-1 flex flex-col min-h-0'

  return (
    <div className={rootClass}>
      {topNav && (
        <header className={topNavClass}>
          {typeof topNav === 'function' ? topNav({ openSidebar }) : topNav}
        </header>
      )}
      <div className={bodyClass}>
        {sidebar && (
          <>
            <aside className={sidebarClass} aria-label="Sidebar">
              {sidebar}
            </aside>
            {sidebarOpen && (
              <>
                <div
                  className={mobileSidebarBackdropClass}
                  onClick={closeSidebar}
                  onKeyDown={(e) => e.key === 'Escape' && closeSidebar()}
                  role="button"
                  tabIndex={0}
                  aria-label="Close sidebar"
                />
                <aside className={mobileSidebarPanelClass} aria-label="Sidebar">
                  {sidebar}
                </aside>
              </>
            )}
          </>
        )}
        <main className={mainClass}>
          <div className={contentClass}>{children}</div>
        </main>
      </div>
    </div>
  )
}

export default AppLayout
