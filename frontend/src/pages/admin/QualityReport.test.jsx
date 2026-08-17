import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import QualityReport from './QualityReport'
import * as evaluation from '../../services/evaluationService'

vi.mock('../../components/layout/AdminLayout', () => ({ default: ({ children }) => <div>{children}</div> }))
vi.mock('../../services/evaluationService', () => ({
  getEvaluationResults: vi.fn(),
  listAllEvaluationRuns: vi.fn(),
}))

const run = (id, correctness) => ({
  id,
  subjectId: 'subject-1',
  status: 'complete',
  corpusVersion: 'v1',
  pipelineSnapshot: { rerank: false },
  summaryMetrics: { correctness, faithfulness: 0.92, citationCoverage: 0.96, errorRate: 0 },
})

describe('admin tutor-quality report', () => {
  beforeEach(() => {
    evaluation.listAllEvaluationRuns.mockResolvedValue([run('run-1', 0.7), run('run-2', 0.85)])
    evaluation.getEvaluationResults.mockResolvedValue([
      { id: 'result-1', caseId: 'case-1', generatedAnswer: 'A weak answer', metrics: { correctness: 0.5 }, failureInfo: null },
    ])
  })

  it('compares two runs and drills into low-scoring cases', async () => {
    render(<QualityReport />)
    const compareBoxes = await screen.findAllByRole('checkbox', { name: 'Compare' })
    fireEvent.click(compareBoxes[0])
    fireEvent.click(compareBoxes[1])
    expect(screen.getByRole('heading', { name: 'Run comparison' })).toBeInTheDocument()
    expect(screen.getByText('0.70 → 0.85')).toBeInTheDocument()

    fireEvent.click(screen.getAllByRole('button', { name: 'Inspect failed cases' })[0])
    await waitFor(() => expect(evaluation.getEvaluationResults).toHaveBeenCalledWith('subject-1', 'run-1'))
    expect(await screen.findByText('Case case-1')).toBeInTheDocument()
    expect(screen.getByText('Correctness 0.50')).toBeInTheDocument()
  })
})
