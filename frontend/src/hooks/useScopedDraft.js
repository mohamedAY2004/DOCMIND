import { useState } from 'react'

export default function useScopedDraft(key) {
  const [draft, setDraft] = useState({ key, text: '' })
  return [draft.key === key ? draft.text : '', (text) => setDraft({ key, text })]
}
