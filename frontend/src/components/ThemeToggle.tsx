import type { Theme } from '../hooks/useTheme'
import { SunIcon, MoonIcon } from './icons'

interface Props {
  theme: Theme
  onToggle: () => void
}

export function ThemeToggle({ theme, onToggle }: Props) {
  const isDark = theme === 'dark'
  return (
    <button
      className="theme-toggle"
      onClick={onToggle}
      role="switch"
      aria-checked={isDark}
      aria-label={isDark ? 'Zu hellem Modus wechseln' : 'Zu dunklem Modus wechseln'}
    >
      <span className={`theme-toggle-knob ${isDark ? 'dark' : ''}`} />
      <span className="theme-toggle-icon sun"><SunIcon /></span>
      <span className="theme-toggle-icon moon"><MoonIcon /></span>
    </button>
  )
}
