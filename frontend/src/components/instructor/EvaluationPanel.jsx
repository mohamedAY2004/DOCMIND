import { useCallback, useEffect, useState } from 'react'
import { Activity, Loader2, MessageSquare, Play, Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import {
  createEvaluationCase,
  convertFeedbackToCase,
  deleteEvaluationCase,
  getEvaluationResults,
  getReadiness,
  listEvaluationCases,
  listEvaluationRuns,
  listTutorFeedback,
  startEvaluationRun,
} from '../../services/evaluationService'

export default function EvaluationPanel({ subjectId }) {
  const [readiness, setReadiness] = useState(null)
  const [cases, setCases] = useState([])
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [question, setQuestion] = useState('')
  const [referenceAnswer, setReferenceAnswer] = useState('')
  const [results, setResults] = useState([])
  const [feedbackRows, setFeedbackRows] = useState([])
  const [feedbackSource, setFeedbackSource] = useState(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const [nextReadiness, nextCases, nextRuns, nextFeedback] = await Promise.all([
        getReadiness(subjectId), listEvaluationCases(subjectId), listEvaluationRuns(subjectId), listTutorFeedback(subjectId),
      ])
      setReadiness(nextReadiness)
      setCases(nextCases)
      setRuns(nextRuns)
      setFeedbackRows(nextFeedback.items || [])
    } catch {
      toast.error('Could not load tutor quality data.')
    } finally {
      setLoading(false)
    }
  }, [subjectId])

  useEffect(() => { void refresh() }, [refresh])

  const addCase = async (event) => {
    event.preventDefault()
    if (!question.trim() || !referenceAnswer.trim()) return
    setCreating(true)
    try {
      const item = feedbackSource
        ? await convertFeedbackToCase(subjectId, feedbackSource.id, {
            referenceAnswer: referenceAnswer.trim(), expectedMaterialIds: [], tags: [],
          })
        : await createEvaluationCase(subjectId, {
            question: question.trim(), referenceAnswer: referenceAnswer.trim(),
            expectedMaterialIds: [], tags: [], active: true,
          })
      setCases((current) => [...current, item])
      if (feedbackSource) {
        setFeedbackRows((current) => current.map((row) => row.id === feedbackSource.id ? { ...row, evaluationCaseId: item.id } : row))
      }
      setQuestion('')
      setReferenceAnswer('')
      setFeedbackSource(null)
    } catch { toast.error('Could not add the evaluation case.') }
    finally { setCreating(false) }
  }

  const runEvaluation = async () => {
    try {
      const run = await startEvaluationRun(subjectId)
      setRuns((current) => [run, ...current])
      toast.success('Evaluation queued for the worker.')
    } catch (err) { toast.error(err?.response?.data?.message || 'Could not queue evaluation.') }
  }

  if (loading) return <div className="flex items-center gap-2 py-8 text-dm-muted"><Loader2 className="animate-spin" size={18} /> Loading quality checks…</div>

  return (
    <section className="rounded-card border border-dm-border bg-dm-card p-6 shadow-xl" aria-labelledby="quality-title">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 id="quality-title" className="flex items-center gap-2 text-lg font-bold text-dm-foreground"><Activity className="text-dm-primary" size={20} /> Tutor readiness</h2>
          <p className="mt-1 text-sm text-dm-muted">Advisory only—students retain access while issues are reviewed.</p>
        </div>
        <span className={`rounded-full px-3 py-1 text-sm font-semibold ${readiness?.state === 'healthy' ? 'bg-emerald-500/15 text-emerald-400' : readiness?.state === 'needs_review' ? 'bg-amber-500/15 text-amber-400' : 'bg-red-500/15 text-red-400'}`}>{readiness?.state?.replace('_', ' ')}</span>
      </div>
      {readiness?.reasons?.length > 0 && <ul className="mt-4 grid gap-2 text-sm text-dm-muted sm:grid-cols-2">{readiness.reasons.map((reason) => <li key={reason} className="rounded-lg bg-dm-background px-3 py-2">{reason.replaceAll('_', ' ')}</li>)}</ul>}
      <div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-4">
        {[['Cases', readiness?.activeCases], ['Correctness', readiness?.metrics?.correctness?.toFixed?.(2) ?? '—'], ['Faithfulness', readiness?.metrics?.faithfulness?.toFixed?.(2) ?? '—'], ['Citation coverage', readiness?.metrics?.citationCoverage?.toFixed?.(2) ?? '—']].map(([label, value]) => <div key={label} className="rounded-xl border border-dm-border bg-dm-background p-3"><p className="text-xs text-dm-muted">{label}</p><p className="mt-1 text-xl font-bold text-dm-foreground">{value ?? '—'}</p></div>)}
      </div>

      <form onSubmit={addCase} className="mt-6 grid gap-3 rounded-xl border border-dm-border bg-dm-background p-4">
        <h3 className="font-semibold text-dm-foreground">Add evaluation case</h3>
        {feedbackSource && <div className="rounded-lg border border-amber-500/20 bg-amber-500/10 p-3 text-sm text-dm-muted"><p className="font-medium text-dm-foreground">Prefilled from reviewed feedback</p><p className="mt-1">Reason: {feedbackSource.reason || 'not specified'}{feedbackSource.comment ? ` · ${feedbackSource.comment}` : ''}</p><button type="button" onClick={() => { setFeedbackSource(null); setQuestion('') }} className="mt-2 text-xs text-dm-primary underline">Clear prefill</button></div>}
        <label className="text-sm text-dm-muted">Question<textarea value={question} onChange={(e) => setQuestion(e.target.value)} rows={2} className="mt-1 w-full rounded-lg border border-dm-border bg-dm-card p-3 text-dm-foreground" required /></label>
        <label className="text-sm text-dm-muted">Reference answer<textarea value={referenceAnswer} onChange={(e) => setReferenceAnswer(e.target.value)} rows={3} className="mt-1 w-full rounded-lg border border-dm-border bg-dm-card p-3 text-dm-foreground" required /></label>
        <button type="submit" disabled={creating} className="inline-flex w-fit items-center gap-2 rounded-lg bg-dm-primary px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"><Plus size={16} /> Add case</button>
      </form>

      <div className="mt-6">
        <h3 className="flex items-center gap-2 font-semibold text-dm-foreground"><MessageSquare size={17} /> Tutor feedback review</h3>
        <p className="mt-1 text-sm text-dm-muted">Only subject tutor feedback appears here; private document chats are excluded.</p>
        <ul className="mt-3 grid gap-2">
          {feedbackRows.filter((row) => row.feedback === 'down').map((row) => <li key={row.id} className="rounded-xl border border-dm-border bg-dm-background p-3"><div className="flex flex-wrap items-start justify-between gap-3"><div className="min-w-0 flex-1"><p className="font-medium text-dm-foreground">{row.question}</p><p className="mt-1 line-clamp-2 text-sm text-dm-muted">{row.aiResponse}</p><p className="mt-2 text-xs text-amber-400">{row.reason || 'negative'}{row.comment ? ` · ${row.comment}` : ''}</p></div><button type="button" disabled={Boolean(row.evaluationCaseId)} onClick={() => { setFeedbackSource(row); setQuestion(row.question); setReferenceAnswer('') }} className="rounded-lg border border-dm-primary/30 px-3 py-2 text-xs font-semibold text-dm-primary disabled:opacity-50">{row.evaluationCaseId ? 'Added' : 'Use as case'}</button></div></li>)}
          {!feedbackRows.some((row) => row.feedback === 'down') && <li className="rounded-xl border border-dashed border-dm-border p-4 text-sm text-dm-muted">No negative tutor feedback to review.</li>}
        </ul>
      </div>

      <div className="mt-6 flex items-center justify-between"><h3 className="font-semibold text-dm-foreground">Question bank ({cases.length})</h3><button type="button" onClick={runEvaluation} disabled={!cases.length || runs.some((run) => ['queued', 'running'].includes(run.status))} className="inline-flex items-center gap-2 rounded-lg bg-dm-primary px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"><Play size={15} /> Run evaluation</button></div>
      <ul className="mt-3 divide-y divide-dm-border rounded-xl border border-dm-border">{cases.map((item) => <li key={item.id} className="flex gap-3 p-3"><div className="min-w-0 flex-1"><p className="font-medium text-dm-foreground">{item.question}</p><p className="mt-1 line-clamp-2 text-sm text-dm-muted">{item.referenceAnswer}</p></div><button type="button" onClick={async () => { await deleteEvaluationCase(subjectId, item.id); setCases((rows) => rows.filter((row) => row.id !== item.id)) }} className="p-2 text-dm-muted hover:text-red-400" aria-label="Delete evaluation case"><Trash2 size={16} /></button></li>)}</ul>

      <h3 className="mt-6 font-semibold text-dm-foreground">Recent runs</h3>
      <div className="mt-3 grid gap-3">{runs.map((run) => <button key={run.id} type="button" onClick={async () => setResults(await getEvaluationResults(subjectId, run.id))} className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-dm-border bg-dm-background p-3 text-left"><span className="text-sm font-medium text-dm-foreground">{run.id}</span><span className="text-sm text-dm-muted">{run.status} · correctness {run.summaryMetrics?.correctness?.toFixed?.(2) ?? '—'}</span></button>)}</div>
      {results.length > 0 && <div className="mt-5"><h3 className="font-semibold text-dm-foreground">Failed and low-scoring cases</h3><ul className="mt-2 grid gap-2">{results.filter((item) => item.failureInfo || item.metrics?.correctness < 0.8).map((item) => <li key={item.id} className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3 text-sm text-dm-muted">Case {item.caseId}: {item.failureInfo?.message || `correctness ${item.metrics.correctness.toFixed(2)}`}</li>)}</ul></div>}
    </section>
  )
}
