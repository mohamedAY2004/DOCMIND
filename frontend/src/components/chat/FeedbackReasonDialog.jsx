import { useEffect, useRef, useState } from 'react'

const reasons = [
  ['incorrect', 'Incorrect'],
  ['unsupported', 'Unsupported by sources'],
  ['outdated', 'Outdated'],
  ['unclear', 'Unclear'],
  ['incomplete', 'Incomplete'],
  ['other', 'Other'],
]

export default function FeedbackReasonDialog({ open, onCancel, onSubmit }) {
  const [reason, setReason] = useState('incorrect')
  const [comment, setComment] = useState('')
  const selectRef = useRef(null)
  const dialogRef = useRef(null)

  useEffect(() => {
    if (!open) return undefined
    const previous = document.activeElement
    selectRef.current?.focus()
    const onKeyDown = (event) => {
      if (event.key === 'Escape') onCancel()
      if (event.key !== 'Tab') return
      const items = [...(dialogRef.current?.querySelectorAll('button,select,textarea,[tabindex]:not([tabindex="-1"])') || [])]
      if (!items.length) return
      const first = items[0]
      const last = items[items.length - 1]
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus() }
      if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
    }
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      previous?.focus?.()
    }
  }, [open, onCancel])
  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="feedback-title"
    >
      <form
        ref={dialogRef}
        className="w-full max-w-md rounded-2xl border border-dm-border bg-dm-card p-5 shadow-2xl"
        onSubmit={(event) => {
          event.preventDefault()
          onSubmit({ reason, comment: comment.trim() || undefined })
          setComment('')
        }}
      >
        <h2 id="feedback-title" className="text-lg font-semibold text-dm-foreground">What went wrong?</h2>
        <p className="mt-1 text-sm text-dm-muted">Your reason helps improve this subject’s tutor.</p>
        <label className="mt-4 block text-sm font-medium text-dm-foreground" htmlFor="feedback-reason">Reason</label>
        <select
          ref={selectRef}
          id="feedback-reason"
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          className="mt-1 w-full rounded-lg border border-dm-border bg-dm-background px-3 py-2 text-dm-foreground focus:ring-2 focus:ring-dm-primary"
        >
          {reasons.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </select>
        <label className="mt-4 block text-sm font-medium text-dm-foreground" htmlFor="feedback-comment">Comment (optional)</label>
        <textarea
          id="feedback-comment"
          value={comment}
          onChange={(event) => setComment(event.target.value)}
          maxLength={500}
          rows={4}
          className="mt-1 w-full resize-y rounded-lg border border-dm-border bg-dm-background px-3 py-2 text-dm-foreground focus:ring-2 focus:ring-dm-primary"
        />
        <div className="mt-5 flex justify-end gap-2">
          <button type="button" onClick={onCancel} className="rounded-lg px-4 py-2 text-sm text-dm-muted hover:bg-dm-background">Cancel</button>
          <button type="submit" className="rounded-lg bg-dm-primary px-4 py-2 text-sm font-semibold text-white hover:opacity-90">Submit feedback</button>
        </div>
      </form>
    </div>
  )
}
