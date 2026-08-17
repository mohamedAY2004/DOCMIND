import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import SourceDrawer from './SourceDrawer'
import { getCitationView } from '../../services/chatService'

vi.mock('../../services/chatService', () => ({
  getCitationView: vi.fn(),
  resolveApiUrl: (url) => url,
}))

describe('citation source drawer', () => {
  it('loads the authorized source metadata and closes by keyboard', async () => {
    getCitationView.mockResolvedValue({
      url: '',
      sourceName: 'Lecture 4',
      locationType: 'page',
      locationNumber: 7,
      excerpt: 'Grounded source excerpt',
    })
    const close = vi.fn()
    render(<SourceDrawer source={{ messageId: 'msg_1', citation: { id: 'cite_1', sourceName: 'Lecture 4', excerpt: 'Fallback', location: { type: 'page', number: 7 } } }} onClose={close} />)
    await waitFor(() => expect(getCitationView).toHaveBeenCalledWith('msg_1', 'cite_1'))
    expect(screen.getByText('Grounded source excerpt')).toBeInTheDocument()
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(close).toHaveBeenCalledOnce()
  })
})
