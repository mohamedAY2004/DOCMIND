import { Sun, Moon } from 'lucide-react'
import useTheme from '../../hooks/useTheme'

const toggleClass =
  'relative flex h-9 w-9 items-center justify-center rounded-lg text-dm-muted transition-colors duration-200 hover:bg-dm-background hover:text-dm-foreground'

function ThemeToggle({ className = '' }) {
  const { theme, toggleTheme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={[toggleClass, className].filter(Boolean).join(' ')}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {isDark ? (
        <Sun size={18} className="text-current" />
      ) : (
        <Moon size={18} className="text-current" />
      )}
    </button>
  )
}

export default ThemeToggle
