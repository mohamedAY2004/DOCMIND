import { createContext, useContext, useState, useEffect, useCallback } from 'react'

const STORAGE_KEY = 'docmind-theme'

const ThemeContext = createContext({ theme: 'dark', toggleTheme: () => {} })

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored === 'light' || stored === 'dark') return stored
    } catch {
      // Storage can be unavailable in privacy-restricted browser contexts.
    }
    return 'dark'
  })

  useEffect(() => {
    const root = document.documentElement
    root.classList.remove('light', 'dark')
    root.classList.add(theme)
    try {
      localStorage.setItem(STORAGE_KEY, theme)
    } catch {
      // Theme still applies to this page when persistence is unavailable.
    }
  }, [theme])

  const toggleTheme = useCallback(() => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))
  }, [])

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export default function useTheme() {
  return useContext(ThemeContext)
}
