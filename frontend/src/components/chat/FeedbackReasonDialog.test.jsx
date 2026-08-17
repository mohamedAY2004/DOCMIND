import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import FeedbackReasonDialog from './FeedbackReasonDialog'

describe('FeedbackReasonDialog', () => {
  it('submits a structured reason and optional comment', () => {
    const submit = vi.fn()
    render(<FeedbackReasonDialog open onCancel={() => {}} onSubmit={submit} />)
    fireEvent.change(screen.getByLabelText('Reason'), { target: { value: 'unsupported' } })
    fireEvent.change(screen.getByLabelText('Comment (optional)'), { target: { value: 'No citation' } })
    fireEvent.click(screen.getByRole('button', { name: 'Submit feedback' }))
    expect(submit).toHaveBeenCalledWith({ reason: 'unsupported', comment: 'No citation' })
  })

  it('closes with Escape and keeps keyboard focus inside', () => {
    const cancel = vi.fn()
    render(<FeedbackReasonDialog open onCancel={cancel} onSubmit={() => {}} />)
    const select = screen.getByLabelText('Reason')
    const submit = screen.getByRole('button', { name: 'Submit feedback' })
    submit.focus()
    fireEvent.keyDown(document, { key: 'Tab' })
    expect(select).toHaveFocus()
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(cancel).toHaveBeenCalledOnce()
  })
})
