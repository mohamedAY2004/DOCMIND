import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, ChevronDown, Loader2, ShieldCheck } from 'lucide-react'
import AdminLayout from '../../components/layout/AdminLayout'
import { getEvaluationResults, listAllEvaluationRuns } from '../../services/evaluationService'

const METRICS = [
  ['Correctness', 'correctness'],
  ['Faithfulness', 'faithfulness'],
  ['Citation coverage', 'citationCoverage'],
  ['Error rate', 'errorRate'],
]

function formatMetric(value) {
  return typeof value === 'number' ? value.toFixed(2) : '—'
}

function runLabel(run) {
  return `${run.subjectId} · ${run.id}`
}

export default function QualityReport() {
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedIds, setSelectedIds] = useState([])
  const [openRunId, setOpenRunId] = useState(null)
  const [resultsByRun, setResultsByRun] = useState({})
  const [resultsLoading, setResultsLoading] = useState(null)
  const [resultsError, setResultsError] = useState(null)

  useEffect(() => {
    let cancelled = false
    listAllEvaluationRuns()
      .then((data) => { if (!cancelled) setRuns(data) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [])

  const selectedRuns = useMemo(
    () => selectedIds.map((id) => runs.find((run) => run.id === id)).filter(Boolean),
    [runs, selectedIds],
  )

  const toggleComparison = (runId) => {
    setSelectedIds((current) => {
      if (current.includes(runId)) return current.filter((id) => id !== runId)
      return [...current.slice(-1), runId]
    })
  }

  const toggleResults = async (run) => {
    if (openRunId === run.id) {
      setOpenRunId(null)
      return
    }
    setOpenRunId(run.id)
    setResultsError(null)
    if (resultsByRun[run.id]) return
    setResultsLoading(run.id)
    try {
      const results = await getEvaluationResults(run.subjectId, run.id)
      setResultsByRun((current) => ({ ...current, [run.id]: results }))
    } catch {
      setResultsError(run.id)
    } finally {
      setResultsLoading(null)
    }
  }

  return (
    <AdminLayout title="Tutor quality">
      <div className="mx-auto max-w-6xl p-6 md:p-10">
        <div className="mb-6 flex items-start gap-3">
          <ShieldCheck className="mt-1 text-dm-primary" />
          <div>
            <h2 className="text-2xl font-bold text-dm-foreground">Cross-subject evaluation runs</h2>
            <p className="text-sm text-dm-muted">Select two runs to compare their metrics, then inspect failed or low-scoring cases.</p>
          </div>
        </div>

        {selectedRuns.length === 2 && (
          <section className="mb-6 rounded-2xl border border-dm-primary/30 bg-dm-primary/5 p-5" aria-labelledby="comparison-title">
            <h3 id="comparison-title" className="font-semibold text-dm-foreground">Run comparison</h3>
            <p className="mt-1 text-xs text-dm-muted">Change is calculated from {runLabel(selectedRuns[0])} to {runLabel(selectedRuns[1])}.</p>
            <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {METRICS.map(([label, key]) => {
                const before = selectedRuns[0].summaryMetrics?.[key]
                const after = selectedRuns[1].summaryMetrics?.[key]
                const delta = typeof before === 'number' && typeof after === 'number' ? after - before : null
                return (
                  <div key={key} className="rounded-xl border border-dm-border bg-dm-card p-3">
                    <p className="text-xs text-dm-muted">{label}</p>
                    <p className="mt-1 text-lg font-bold text-dm-foreground">{formatMetric(before)} → {formatMetric(after)}</p>
                    <p className={`text-xs ${delta === null ? 'text-dm-muted' : delta >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      {delta === null ? 'No comparable values' : `${delta >= 0 ? '+' : ''}${delta.toFixed(2)}`}
                    </p>
                  </div>
                )
              })}
            </div>
          </section>
        )}

        {loading ? (
          <div className="flex items-center gap-2 py-12 text-dm-muted"><Loader2 className="animate-spin" /> Loading runs…</div>
        ) : (
          <div className="grid gap-4">
            {runs.map((run) => {
              const metrics = run.summaryMetrics || {}
              const healthy = metrics.correctness >= 0.8 && metrics.faithfulness >= 0.9 && metrics.citationCoverage >= 0.95
              const runResults = resultsByRun[run.id] || []
              const problemResults = runResults.filter((item) => item.failureInfo || item.metrics?.correctness < 0.8)
              const isSelected = selectedIds.includes(run.id)
              const isOpen = openRunId === run.id
              return (
                <article key={run.id} className="rounded-2xl border border-dm-border bg-dm-card p-5">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h3 className="font-semibold text-dm-foreground">{run.subjectId}</h3>
                      <p className="text-xs text-dm-muted">{run.id} · corpus {run.corpusVersion}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <label className="flex cursor-pointer items-center gap-2 text-xs text-dm-muted">
                        <input type="checkbox" checked={isSelected} onChange={() => toggleComparison(run.id)} className="h-4 w-4 accent-dm-primary" />
                        Compare
                      </label>
                      <span className={`rounded-full px-3 py-1 text-xs font-semibold ${healthy ? 'bg-emerald-500/15 text-emerald-400' : 'bg-amber-500/15 text-amber-400'}`}>{run.status}</span>
                    </div>
                  </div>
                  <div className="mt-4 grid grid-cols-2 gap-2 md:grid-cols-4">
                    {METRICS.map(([label, key]) => <div key={key} className="rounded-lg bg-dm-background p-3"><p className="text-xs text-dm-muted">{label}</p><p className="text-lg font-bold text-dm-foreground">{formatMetric(metrics[key])}</p></div>)}
                  </div>
                  <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-sm">
                    <button type="button" onClick={() => void toggleResults(run)} aria-expanded={isOpen} className="inline-flex items-center gap-1 text-dm-primary">
                      <ChevronDown size={16} className={isOpen ? 'rotate-180' : ''} /> Inspect failed cases
                    </button>
                    <details>
                      <summary className="cursor-pointer text-dm-primary">Pipeline snapshot</summary>
                      <pre className="mt-2 max-w-full overflow-auto rounded-lg bg-dm-background p-3 text-xs text-dm-muted">{JSON.stringify(run.pipelineSnapshot, null, 2)}</pre>
                    </details>
                  </div>
                  {isOpen && (
                    <div className="mt-4 border-t border-dm-border pt-4">
                      {resultsLoading === run.id && <p className="flex items-center gap-2 text-sm text-dm-muted"><Loader2 className="animate-spin" size={16} /> Loading case results…</p>}
                      {resultsError === run.id && <p className="text-sm text-red-400">Case results could not be loaded.</p>}
                      {resultsByRun[run.id] && problemResults.length === 0 && <p className="text-sm text-emerald-400">No failed or low-scoring cases in this run.</p>}
                      {problemResults.length > 0 && (
                        <ul className="grid gap-3">
                          {problemResults.map((item) => (
                            <li key={item.id} className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4">
                              <p className="flex items-center gap-2 text-sm font-semibold text-dm-foreground"><AlertTriangle size={16} className="text-amber-400" /> Case {item.caseId}</p>
                              <p className="mt-1 text-sm text-dm-muted">{item.failureInfo?.message || `Correctness ${formatMetric(item.metrics?.correctness)}`}</p>
                              {item.generatedAnswer && <details className="mt-2 text-sm"><summary className="cursor-pointer text-dm-primary">Generated answer</summary><p className="mt-2 whitespace-pre-wrap text-dm-muted">{item.generatedAnswer}</p></details>}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  )}
                </article>
              )
            })}
            {!runs.length && <p className="rounded-xl border border-dashed border-dm-border p-10 text-center text-dm-muted">No evaluation runs yet.</p>}
          </div>
        )}
      </div>
    </AdminLayout>
  )
}
