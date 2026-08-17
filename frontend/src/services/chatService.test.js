import { afterEach, describe, expect, it, vi } from 'vitest'
import apiClient from './apiClient'
import { parseSseFrame, streamDocMessage, streamMessage } from './chatService'

afterEach(() => {
  vi.restoreAllMocks()
  vi.useRealTimers()
})

describe('chat SSE parser', () => {
  it('parses named JSON events', () => {
    expect(parseSseFrame('event: answer.delta\ndata: {"replyId":"r1","delta":"Hi"}')).toEqual({
      event: 'answer.delta',
      data: { replyId: 'r1', delta: 'Hi' },
    })
  })

  it('ignores empty frames', () => {
    expect(parseSseFrame('')).toBeNull()
  })

  it('falls back to the compatible endpoint when streaming is disabled', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      status: 404,
      ok: false,
      json: async () => ({ message: 'Streaming chat is disabled.' }),
    })
    const response = {
      userMessage: { id: 'user-1', role: 'user', text: 'Hello' },
      reply: { id: 'reply-1', role: 'doc', text: 'Buffered answer' },
    }
    vi.spyOn(apiClient, 'post').mockResolvedValue({ data: response })
    const events = []
    await streamDocMessage('conv-1', 'Hello', {
      onEvent: (event, payload) => events.push([event, payload]),
    })
    expect(apiClient.post).toHaveBeenCalledWith(
      '/chat/doc/conversations/conv-1/messages',
      { message: 'Hello' },
      expect.any(Object),
    )
    expect(events.map(([event]) => event)).toEqual([
      'message.created',
      'answer.completed',
    ])
  })

  it('times out if no stream headers arrive', async () => {
    vi.useFakeTimers()
    vi.spyOn(globalThis, 'fetch').mockImplementation((_url, options) => (
      new Promise((_resolve, reject) => {
        options.signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')))
      })
    ))
    const expectation = expect(streamMessage('/chat/test', 'Hello')).rejects.toThrow(
      'The response timed out',
    )
    await vi.advanceTimersByTimeAsync(60_000)
    await expectation
  })
})
