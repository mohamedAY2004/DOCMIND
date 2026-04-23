import { useCallback, useState } from 'react'
import {
  Loader2,
  MessageCircle,
  MoreHorizontal,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  Trash2,
  X,
} from 'lucide-react'

const toggleBtnClass =
  'flex h-8 w-8 items-center justify-center rounded-lg text-dm-muted hover:bg-dm-background hover:text-dm-foreground transition-colors'

const chatBtnBase =
  'flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors duration-200'
const chatBtnActive =
  'border-l-2 border-dm-primary bg-dm-primary/15 text-dm-foreground shadow-sm shadow-dm-primary/10'
const chatBtnInactive =
  'border-l-2 border-transparent text-dm-muted hover:bg-dm-background hover:text-dm-foreground'

const actionBtnClass =
  'flex h-6 w-6 shrink-0 items-center justify-center rounded text-dm-muted transition-all duration-150'
const deleteBtnClass =
  'flex h-6 w-6 shrink-0 items-center justify-center rounded text-red-400 hover:text-red-300 hover:bg-red-400/10 transition-colors'
const cancelBtnClass =
  'flex h-6 w-6 shrink-0 items-center justify-center rounded text-dm-muted hover:text-dm-foreground hover:bg-dm-background transition-colors'

/**
 * Controlled conversation list. The parent owns the list and the active id;
 * the sidebar only renders them and forwards user intents.
 */
function ChatSidebar({
  chats = [],
  activeId = null,
  onSelectChat,
  onNewChat,
  onDeleteChat,
  loading = false,
  emptyLabel = 'No conversations yet.',
}) {
  const [collapsed, setCollapsed] = useState(false)
  const [confirmDeleteId, setConfirmDeleteId] = useState(null)

  const toggle = useCallback(() => {
    setCollapsed((prev) => !prev)
    setConfirmDeleteId(null)
  }, [])

  const handleDelete = useCallback(
    (id) => {
      setConfirmDeleteId(null)
      onDeleteChat?.(id)
    },
    [onDeleteChat],
  )

  return (
    <aside
      className={`hidden lg:flex h-full shrink-0 flex-col border-r border-dm-border bg-dm-card transition-all duration-300 ease-in-out overflow-hidden ${
        collapsed ? 'w-16' : 'w-64'
      }`}
    >
      {/* Header */}
      <div
        className={`flex shrink-0 items-center border-b border-dm-border/50 px-3 py-3 ${
          collapsed ? 'justify-center' : 'justify-between'
        }`}
      >
        {!collapsed && (
          <span className="text-sm font-medium text-dm-muted whitespace-nowrap">
            History
          </span>
        )}
        <button
          type="button"
          onClick={toggle}
          className={toggleBtnClass}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? (
            <PanelLeftOpen size={18} className="text-current" />
          ) : (
            <PanelLeftClose size={18} className="text-current" />
          )}
        </button>
      </div>

      {/* Chat list */}
      <nav className="flex-1 overflow-y-auto p-2 flex flex-col gap-1">
        {loading && chats.length === 0 ? (
          <div className="flex items-center justify-center gap-2 px-3 py-6 text-sm text-dm-muted">
            <Loader2 size={14} className="animate-spin" />
            {!collapsed && <span>Loading…</span>}
          </div>
        ) : chats.length === 0 ? (
          !collapsed && (
            <p className="px-3 py-6 text-center text-xs text-dm-muted/70">
              {emptyLabel}
            </p>
          )
        ) : (
          chats.map((chat) => {
            const label = chat.title || chat.label || 'Untitled chat'
            return (
              <div
                key={chat.id}
                className="group relative flex items-center"
              >
                <button
                  type="button"
                  onClick={() => onSelectChat?.(chat.id)}
                  className={`${chatBtnBase} ${
                    chat.id === activeId ? chatBtnActive : chatBtnInactive
                  }`}
                  title={collapsed ? label : undefined}
                >
                  <MessageCircle size={18} className="shrink-0" />
                  {!collapsed && (
                    <span className="truncate whitespace-nowrap">{label}</span>
                  )}
                </button>

                {/* Hover actions — expanded only */}
                {!collapsed && onDeleteChat && (
                  <div className="absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-0.5">
                    {confirmDeleteId === chat.id ? (
                      <>
                        <button
                          type="button"
                          onClick={() => handleDelete(chat.id)}
                          className={deleteBtnClass}
                          aria-label="Confirm delete"
                        >
                          <Trash2 size={13} />
                        </button>
                        <button
                          type="button"
                          onClick={() => setConfirmDeleteId(null)}
                          className={cancelBtnClass}
                          aria-label="Cancel delete"
                        >
                          <X size={13} />
                        </button>
                      </>
                    ) : (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation()
                          setConfirmDeleteId(chat.id)
                        }}
                        className={`${actionBtnClass} opacity-0 group-hover:opacity-100 hover:bg-dm-background hover:text-dm-foreground`}
                        aria-label="Chat options"
                      >
                        <MoreHorizontal size={15} />
                      </button>
                    )}
                  </div>
                )}
              </div>
            )
          })
        )}
      </nav>

      {/* New chat button */}
      <div className="shrink-0 border-t border-dm-border/50 p-2">
        <button
          type="button"
          onClick={onNewChat}
          className={`flex w-full items-center justify-center gap-2 rounded-xl bg-dm-primary py-2.5 px-4 font-medium text-dm-foreground transition-opacity hover:opacity-90 active:scale-[0.98] ${
            collapsed ? 'px-0' : ''
          }`}
        >
          <Plus size={18} className="shrink-0" />
          {!collapsed && <span className="whitespace-nowrap">New Chat</span>}
        </button>
      </div>
    </aside>
  )
}

export default ChatSidebar
