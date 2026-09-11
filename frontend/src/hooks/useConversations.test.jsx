import { act, renderHook, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import useConversations from './useConversations'

describe('conversation lists', () => {
  it('does not let a pending refresh overwrite successful changes or a new selection', async () => {
    let finish
    const fetcher = vi.fn().mockResolvedValueOnce({ items: [{ id: 'old', title: 'Old' }], page: 1, totalPages: 1 })
      .mockImplementationOnce(() => new Promise((resolve) => { finish = resolve }))
    const remover = vi.fn().mockResolvedValue({})
    const { result } = renderHook(() => useConversations({ fetcher, remover, autoSelectFirst: true }))
    await waitFor(() => expect(result.current.conversations).toHaveLength(1))
    act(() => { void result.current.refresh() })
    await act(async () => { await result.current.deleteConversation('old') })
    act(() => {
      result.current.prependConversation({ id: 'new', title: 'New' })
      result.current.updateConversation('new', { title: 'Updated' })
    })
    await act(async () => { finish({ items: [{ id: 'old', title: 'Old' }], page: 1, totalPages: 1 }) })
    expect(result.current.conversations).toEqual([{ id: 'new', title: 'Updated' }])
    expect(result.current.activeId).toBe('new')
  })
  it('loads conversations beyond the first twenty', async () => {
    const fetcher = vi.fn(async ({ page }) => ({ page, totalPages: 2,
      items: Array.from({ length: page === 1 ? 20 : 3 }, (_, index) => ({ id: `${page}-${index}` })) }))
    const { result } = renderHook(() => useConversations({ fetcher }))
    await waitFor(() => expect(result.current.conversations).toHaveLength(20))
    await act(async () => { await result.current.loadMore() })
    expect(result.current.conversations).toHaveLength(23)
    expect(result.current.hasMore).toBe(false)
  })

  it('ignores list responses and failed mutations from the previous subject', async () => {
    let resolveOld
    let rejectDelete
    const old = new Promise((resolve) => { resolveOld = resolve })
    const removal = new Promise((_resolve, reject) => { rejectDelete = reject })
    const first = vi.fn().mockResolvedValueOnce({ items: [{ id: 'old' }], page: 1, totalPages: 1 }).mockReturnValue(old)
    const second = vi.fn().mockResolvedValue({ items: [{ id: 'new' }], page: 1, totalPages: 1 })
    const remover = vi.fn(() => removal)
    const { result, rerender } = renderHook(({ subject }) => useConversations({ fetcher: subject === 'a' ? first : second, signalKey: subject, remover }), { initialProps: { subject: 'a' } })
    await waitFor(() => expect(result.current.conversations[0]?.id).toBe('old'))
    act(() => { void result.current.deleteConversation('old'); void result.current.refresh() })
    rerender({ subject: 'b' })
    await waitFor(() => expect(result.current.conversations[0]?.id).toBe('new'))
    await act(async () => { resolveOld({ items: [{ id: 'stale' }], page: 1, totalPages: 1 }); rejectDelete(new Error('old failure')) })
    expect(result.current.conversations).toEqual([{ id: 'new' }])
  })
})
