import { useState } from 'react'
import { AlertTriangle, Loader2 } from 'lucide-react'
import Modal from './Modal'
import { primaryButtonCompactClass } from '../../constants/themeClasses'

function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title = 'Confirm action',
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  destructive = false,
}) {
  const [busy, setBusy] = useState(false)

  const handleConfirm = async () => {
    setBusy(true)
    try {
      await onConfirm?.()
      onClose?.()
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal open={open} onClose={busy ? undefined : onClose} title={title} size="sm">
      <div className="flex items-start gap-3">
        {destructive && (
          <span className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-red-400/10 text-red-400">
            <AlertTriangle size={20} />
          </span>
        )}
        <p className="text-sm text-dm-foreground/90">{message}</p>
      </div>
      <div className="mt-6 flex items-center justify-end gap-2">
        <button
          type="button"
          onClick={onClose}
          disabled={busy}
          className="rounded-xl border border-dm-border bg-dm-card px-4 py-2 text-sm font-medium text-dm-muted transition-colors hover:bg-dm-background hover:text-dm-foreground disabled:opacity-50"
        >
          {cancelLabel}
        </button>
        <button
          type="button"
          onClick={handleConfirm}
          disabled={busy}
          className={`flex items-center gap-1.5 rounded-xl px-4 py-2 text-sm font-semibold transition-colors disabled:opacity-60 ${
            destructive
              ? 'bg-red-500/90 text-white hover:bg-red-500'
              : `${primaryButtonCompactClass} hover:opacity-90`
          }`}
        >
          {busy && <Loader2 size={14} className="animate-spin" />}
          {confirmLabel}
        </button>
      </div>
    </Modal>
  )
}

export default ConfirmDialog
