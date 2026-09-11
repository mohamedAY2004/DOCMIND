/** Validate the public pagination contract at the HTTP boundary. */
export function parsePage(data) {
  if (!data || !Array.isArray(data.items)
    || !['page', 'pageSize', 'total', 'totalPages'].every((key) => Number.isInteger(data[key]))
    || data.page < 1 || data.pageSize < 1 || data.total < 0 || data.totalPages < 0) {
    throw new Error('The server returned an invalid paginated response.')
  }
  return data
}

/** For finite selector/export datasets; tables should request individual pages. */
export async function collectPages(fetchPage, { signal, ...params } = {}) {
  const items = []
  let page = 1
  let totalPages
  do {
    signal?.throwIfAborted()
    const response = parsePage(await fetchPage({ ...params, page, signal }))
    items.push(...response.items)
    totalPages = response.totalPages
    page += 1
  } while (page <= totalPages)
  return items
}

/** Some official endpoints deliberately return an unpaginated list. */
export function parseList(data) {
  if (!Array.isArray(data)) throw new Error('The server returned an invalid list response.')
  return data
}
