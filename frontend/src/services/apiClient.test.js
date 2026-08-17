import { afterEach, describe, expect, it, vi } from 'vitest'
import apiClient, { refreshBrowserSession } from './apiClient'

afterEach(() => vi.restoreAllMocks())

describe('browser session refresh', () => {
  it('shares one rotating refresh request across concurrent callers', async () => {
    let resolveRefresh
    const pending = new Promise((resolve) => { resolveRefresh = resolve })
    vi.spyOn(apiClient, 'post').mockReturnValue(pending)
    const first = refreshBrowserSession()
    const second = refreshBrowserSession()
    expect(first).toBe(second)
    expect(apiClient.post).toHaveBeenCalledTimes(1)
    resolveRefresh({ data: {} })
    await Promise.all([first, second])
  })
})
