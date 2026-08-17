import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import EvaluationPanel from './EvaluationPanel'
import * as evaluation from '../../services/evaluationService'

vi.mock('../../services/evaluationService', () => ({
  createEvaluationCase: vi.fn(),
  convertFeedbackToCase: vi.fn(),
  deleteEvaluationCase: vi.fn(),
  getEvaluationResults: vi.fn(),
  getReadiness: vi.fn(),
  listEvaluationCases: vi.fn(),
  listEvaluationRuns: vi.fn(),
  listTutorFeedback: vi.fn(),
  startEvaluationRun: vi.fn(),
}))

describe('instructor tutor-quality journey', () => {
  beforeEach(() => {
    evaluation.getReadiness.mockResolvedValue({ state: 'needs_setup', reasons: ['fewer_than_20_active_cases'], activeCases: 0, metrics: {} })
    evaluation.listEvaluationCases.mockResolvedValue([])
    evaluation.listEvaluationRuns.mockResolvedValue([])
    evaluation.listTutorFeedback.mockResolvedValue({ items: [{ id: 'fb_1', feedback: 'down', question: 'What is entropy?', aiResponse: 'Bad answer', reason: 'incorrect', comment: 'Wrong definition' }] })
    evaluation.convertFeedbackToCase.mockResolvedValue({ id: 'ec_1', question: 'What is entropy?', referenceAnswer: 'Correct definition' })
  })

  it('prefills reviewed feedback and requires an instructor reference answer', async () => {
    render(<EvaluationPanel subjectId="sub_1" />)
    await screen.findByText('What is entropy?')
    fireEvent.click(screen.getByRole('button', { name: 'Use as case' }))
    expect(screen.getByLabelText('Question')).toHaveValue('What is entropy?')
    fireEvent.change(screen.getByLabelText('Reference answer'), { target: { value: 'Correct definition' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add case' }))
    await waitFor(() => expect(evaluation.convertFeedbackToCase).toHaveBeenCalledWith('sub_1', 'fb_1', expect.objectContaining({ referenceAnswer: 'Correct definition' })))
  })
})
