import { useCallback, useEffect, useRef, useState } from 'react'
import { ExternalLink, Loader2, X } from 'lucide-react'
import { getCitationView, resolveApiUrl } from '../../services/chatService'

export default function SourceDrawer({ source, onClose }) {
  const [view, setView] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const canvasRef = useRef(null)
  const drawerRef = useRef(null)

  const loadView = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      setView(await getCitationView(source.messageId, source.citation.id))
    } catch (err) {
      setError(err?.response?.data?.message || 'Could not open this source.')
    } finally {
      setLoading(false)
    }
  }, [source])

  useEffect(() => { void loadView() }, [loadView])

  useEffect(() => {
    if (!view?.url || !canvasRef.current) return
    let cancelled = false
    let task = null
    const render = async () => {
      try {
        const pdfjs = await import('pdfjs-dist')
        pdfjs.GlobalWorkerOptions.workerSrc = new URL(
          'pdfjs-dist/build/pdf.worker.min.mjs', import.meta.url,
        ).toString()
        task = pdfjs.getDocument(resolveApiUrl(view.url))
        const pdf = await task.promise
        const pageNumber = Math.min(Math.max(view.locationNumber || 1, 1), pdf.numPages)
        const page = await pdf.getPage(pageNumber)
        const available = Math.min(drawerRef.current?.clientWidth - 48 || 640, 760)
        const base = page.getViewport({ scale: 1 })
        const viewport = page.getViewport({ scale: available / base.width })
        if (cancelled) return
        const canvas = canvasRef.current
        const ratio = window.devicePixelRatio || 1
        canvas.width = viewport.width * ratio
        canvas.height = viewport.height * ratio
        canvas.style.width = `${viewport.width}px`
        canvas.style.height = `${viewport.height}px`
        await page.render({ canvasContext: canvas.getContext('2d'), viewport, transform: ratio === 1 ? null : [ratio, 0, 0, ratio, 0, 0] }).promise
      } catch {
        if (!cancelled) setError('The signed source link expired or the PDF could not be rendered. Refresh it and try again.')
      }
    }
    void render()
    return () => { cancelled = true; task?.destroy() }
  }, [view])

  useEffect(() => {
    const drawer = drawerRef.current
    const focusable = () => [...(drawer?.querySelectorAll('button,a,[tabindex]:not([tabindex="-1"])') || [])]
    drawer?.querySelector('button')?.focus()
    const onKey = (event) => {
      if (event.key === 'Escape') onClose()
      if (event.key !== 'Tab') return
      const items = focusable()
      if (!items.length) return
      const first = items[0]
      const last = items[items.length - 1]
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus() }
      if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div className="fixed inset-0 z-50 bg-black/60" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose() }}>
      <aside ref={drawerRef} className="ml-auto flex h-full w-full max-w-3xl flex-col border-l border-dm-border bg-dm-background shadow-2xl" role="dialog" aria-modal="true" aria-labelledby="source-title">
        <header className="flex items-start gap-3 border-b border-dm-border p-4">
          <div className="min-w-0 flex-1">
            <h2 id="source-title" className="truncate text-lg font-semibold text-dm-foreground">{view?.sourceName || source.citation.sourceName}</h2>
            <p className="text-sm text-dm-muted">{source.citation.location?.type} {source.citation.location?.number}{source.citation.section ? ` · ${source.citation.section}` : ''}</p>
          </div>
          {view?.url && <a href={resolveApiUrl(view.url)} target="_blank" rel="noreferrer" className="rounded-lg p-2 text-dm-muted hover:bg-dm-card" aria-label="Open source in a new tab"><ExternalLink size={18} /></a>}
          <button type="button" onClick={onClose} className="rounded-lg p-2 text-dm-muted hover:bg-dm-card" aria-label="Close source viewer"><X size={20} /></button>
        </header>
        <div className="flex-1 overflow-auto p-4">
          <blockquote className="mb-4 rounded-xl border border-dm-border bg-dm-card p-3 text-sm text-dm-muted">{view?.excerpt || source.citation.excerpt}</blockquote>
          {loading && <div className="flex items-center justify-center gap-2 py-16 text-dm-muted"><Loader2 className="animate-spin" size={18} /> Loading source…</div>}
          {error && <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">{error}<button type="button" onClick={loadView} className="ml-2 underline">Refresh link</button></div>}
          <canvas ref={canvasRef} className="mx-auto max-w-full rounded shadow-xl" aria-label="Rendered cited PDF page" />
        </div>
      </aside>
    </div>
  )
}
