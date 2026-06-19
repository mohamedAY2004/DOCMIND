import useTheme from '../../hooks/useTheme'

export const PIE_COLORS = ['#22c55e', '#ef4444']

export const TIME_RANGES = [
  { id: 7, label: 'Last 7 days' },
  { id: 14, label: 'Last 14 days' },
  { id: 30, label: 'Last 30 days' },
  { id: 90, label: 'Last 90 days' },
]

export function unwrapList(res) {
  if (!res) return []
  if (Array.isArray(res)) return res
  if (Array.isArray(res.items)) return res.items
  return []
}

export function subjectLabel(title) {
  const t = title || ''
  return t.length > 12 ? `${t.slice(0, 12)}…` : t
}

export function useChartColors() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  return {
    axis: { fill: isDark ? '#8AA3A5' : '#5F7A7C', fontSize: 12 },
    grid: { strokeDasharray: '3 3', stroke: isDark ? '#1F3A3B' : '#D4DEDE' },
    legendColor: isDark ? '#8AA3A5' : '#5F7A7C',
  }
}
