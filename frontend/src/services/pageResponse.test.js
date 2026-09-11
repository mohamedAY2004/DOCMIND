import { describe, expect, it, vi } from 'vitest'
import { collectPages, parseList, parsePage } from './pageResponse'

describe('response contracts', () => {
  it('rejects malformed pages and lists instead of returning empty data', () => {
    for (const value of [null, [], { items: [] }, { items: [], page: 0, pageSize: 20, total: 0, totalPages: 0 }]) {
      expect(() => parsePage(value)).toThrow('invalid paginated response')
    }
    expect(() => parseList({ items: [] })).toThrow('invalid list response')
  })

  it('loads selector datasets beyond the former 1,000-record cap', async () => {
    const fetcher = vi.fn(async ({ page }) => ({ page, pageSize: 100, total: 1001, totalPages: 11,
      items: Array.from({ length: page === 11 ? 1 : 100 }, (_, index) => ({ id: (page - 1) * 100 + index })) }))
    const items = await collectPages(fetcher, { pageSize: 100 })
    expect(items).toHaveLength(1001)
    expect(items.at(-1).id).toBe(1000)
    expect(fetcher).toHaveBeenCalledTimes(11)
  })

  it('stops collecting when the consumer aborts', async () => {
    const controller = new AbortController()
    const fetcher = vi.fn(async () => {
      controller.abort()
      return { items: [], page: 1, pageSize: 100, total: 200, totalPages: 2 }
    })
    await expect(collectPages(fetcher, { signal: controller.signal })).rejects.toThrow()
    expect(fetcher).toHaveBeenCalledTimes(1)
  })
})
