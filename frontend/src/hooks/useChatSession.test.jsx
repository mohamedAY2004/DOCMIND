import { act, renderHook, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import useChatSession from './useChatSession'

vi.mock('../services/chatService', () => ({ cancelMessage: vi.fn().mockResolvedValue({}) }))

const deferred = () => { let resolve; let reject; const promise = new Promise((yes, no) => { resolve = yes; reject = no }); return { promise, resolve, reject } }
const message = (id, text = id) => ({ id, role: 'doc', text, generationStatus: 'complete' })
const page = (items = [], current = 1, totalPages = 1) => ({ items, page: current, pageSize: 50, total: items.length, totalPages })
const setup = (overrides = {}) => {
  const adapter = { role: 'doc', welcome: [], history: vi.fn().mockResolvedValue(page()), stream: vi.fn(), ...overrides }
  const hook = renderHook(({ id }) => useChatSession({ conversationId: id, adapter }), { initialProps: { id: 'a' } })
  return { ...hook, adapter }
}

describe('chat request ownership', () => {
  it('ignores late stream events and completion after switching conversations', async () => {
    const old = deferred()
    let streamOptions
    const hook = setup({ stream: vi.fn((_id, _text, options) => { streamOptions = options; return old.promise }) })
    await waitFor(() => expect(hook.result.current.loadingHistory).toBe(false))
    act(() => { void hook.result.current.sendMessage('old question') })
    hook.rerender({ id: 'b' })
    await waitFor(() => expect(hook.result.current.loadingHistory).toBe(false))
    expect(streamOptions.signal.aborted).toBe(true)
    await act(async () => {
      streamOptions.onEvent('message.created', { userMessage: { id: 'u', role: 'user', text: 'old' }, reply: message('r') })
      streamOptions.onEvent('answer.delta', { replyId: 'r', delta: 'stale' })
      old.resolve()
    })
    expect(hook.result.current.messages).toEqual([])
    expect(hook.result.current.errorMessage).toBe('')
  })

  it('aborts on unmount and rejects delayed history from a previous selection', async () => {
    const old = deferred()
    const hook = setup({ history: vi.fn((id) => id === 'a' ? old.promise : Promise.resolve(page([message('new')]))) })
    const signal = hook.adapter.history.mock.calls[0][1].signal
    hook.rerender({ id: 'b' })
    await waitFor(() => expect(hook.result.current.messages[0]?.id).toBe('new'))
    await act(async () => { old.resolve(page([message('old')])) })
    expect(hook.result.current.messages[0].id).toBe('new')
    expect(signal.aborted).toBe(true)
    hook.unmount()
  })

  it('loads recent history first and prepends older messages chronologically', async () => {
    const hook = setup({ history: vi.fn((_id, options) => Promise.resolve(options.page === 1
      ? page([message('52'), message('51')], 1, 2) : page([message('2'), message('1')], 2, 2))) })
    await waitFor(() => expect(hook.result.current.hasOlderMessages).toBe(true))
    expect(hook.adapter.history.mock.calls[0][1].order).toBe('desc')
    expect(hook.result.current.messages.map((item) => item.id)).toEqual(['51', '52'])
    await act(async () => { await hook.result.current.loadOlder() })
    expect(hook.result.current.messages.map((item) => item.id)).toEqual(['1', '2', '51', '52'])
    expect(hook.result.current.hasOlderMessages).toBe(false)
  })

  it('keeps a retry active when a cancelled request finishes late', async () => {
    const first = deferred()
    const second = deferred()
    const hook = setup({ stream: vi.fn().mockImplementationOnce(() => first.promise).mockImplementationOnce(() => second.promise) })
    await waitFor(() => expect(hook.result.current.loadingHistory).toBe(false))
    act(() => { void hook.result.current.sendMessage('question') })
    act(() => { hook.result.current.stopGeneration() })
    act(() => { void hook.result.current.retry() })
    await act(async () => { first.reject(new DOMException('Aborted', 'AbortError')) })
    expect(hook.result.current.isTyping).toBe(true)
    expect(hook.result.current.errorMessage).toBe('')
    await act(async () => {
      const options = hook.adapter.stream.mock.calls[1][2]
      options.onEvent('message.created', { userMessage: { id: 'u', role: 'user', text: 'question' }, reply: message('r') })
      options.onEvent('answer.completed', { reply: message('r', 'answer') })
      second.resolve()
    })
    expect(hook.result.current.status).toBe('idle')
    expect(hook.result.current.messages.at(-1).text).toBe('answer')
  })

  it('prevents overlapping sends while creating a tutor conversation', async () => {
    const creation = deferred()
    const create = vi.fn(() => creation.promise)
    const onConversationCreated = vi.fn()
    const adapter = { role: 'assistant', welcome: [], history: vi.fn(), create,
      stream: vi.fn(async (_id, _text, { onEvent }) => {
        onEvent('message.created', { userMessage: { id: 'u', role: 'user', text: 'question' }, reply: message('r') })
        onEvent('answer.completed', { reply: message('r') })
      }) }
    const { result, rerender } = renderHook(({ id }) => useChatSession({ conversationId: id, scopeId: 'subject', adapter, onConversationCreated }), { initialProps: { id: null } })
    act(() => { void result.current.sendMessage('one'); void result.current.sendMessage('two') })
    expect(create).toHaveBeenCalledTimes(1)
    await act(async () => { creation.resolve({ id: 'created' }) })
    rerender({ id: 'created' })
    expect(adapter.history).not.toHaveBeenCalled()
    expect(result.current.messages.at(-1).id).toBe('r')
  })
})
