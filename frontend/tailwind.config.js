import typographyPlugin from '@tailwindcss/typography'

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Poppins', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      colors: {
        dm: {
          background: '#0F1C1D',
          card: '#142B2C',
          primary: '#0D6E73',
          muted: '#8AA3A5',
          border: '#1F3A3B',
          foreground: '#FFFFFF',
          statusProcessed: '#22c55e',
          statusIndexing: '#f59e0b',
        },
      },
      borderRadius: {
        'card': '24px',
      },
      typography: (theme) => ({
        DEFAULT: {
          css: {
            '--tw-prose-body': theme('colors.dm.foreground'),
            '--tw-prose-headings': theme('colors.dm.foreground'),
            '--tw-prose-links': theme('colors.dm.primary'),
            '--tw-prose-bold': theme('colors.dm.foreground'),
            '--tw-prose-code': theme('colors.dm.primary'),
            '--tw-prose-pre-bg': theme('colors.dm.background'),
            '--tw-prose-pre-code': theme('colors.dm.foreground'),
            '--tw-prose-quotes': theme('colors.dm.muted'),
            '--tw-prose-quote-borders': theme('colors.dm.primary'),
            '--tw-prose-counters': theme('colors.dm.muted'),
            '--tw-prose-bullets': theme('colors.dm.muted'),
            '--tw-prose-hr': theme('colors.dm.border'),
            '--tw-prose-th-borders': theme('colors.dm.border'),
            '--tw-prose-td-borders': theme('colors.dm.border'),
          },
        },
      }),
      keyframes: {
        'float': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-8px)' },
        },
        'fade-scale-in': {
          '0%': { opacity: '0', transform: 'scale(0.94)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        'fade-scale-out': {
          '0%': { opacity: '1', transform: 'scale(1)' },
          '100%': { opacity: '0', transform: 'scale(0.94)' },
        },
        'pulse-glow': {
          '0%, 100%': { opacity: '0.4', transform: 'scale(1)' },
          '50%': { opacity: '0.8', transform: 'scale(1.08)' },
        },
        'message-in': {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'typing-dot': {
          '0%, 60%, 100%': { opacity: '0.4', transform: 'translateY(0)' },
          '30%': { opacity: '1', transform: 'translateY(-4px)' },
        },
        'breathe-glow': {
          '0%, 100%': { filter: 'drop-shadow(0 0 6px rgba(74,222,128,0.1))' },
          '50%': { filter: 'drop-shadow(0 0 28px rgba(74,222,128,0.55))' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
      animation: {
        'float': 'float 3s ease-in-out infinite',
        'fade-scale-in': 'fade-scale-in 0.5s cubic-bezier(0.16,1,0.3,1) both',
        'fade-scale-out': 'fade-scale-out 0.35s ease-in both',
        'pulse-glow': 'pulse-glow 2.5s ease-in-out infinite',
        'message-in': 'message-in 0.25s ease-out both',
        'typing-dot': 'typing-dot 1.4s ease-in-out infinite',
        'breathe-glow': 'breathe-glow 3s ease-in-out infinite',
        'float-glow': 'float 3s ease-in-out infinite, breathe-glow 3s ease-in-out infinite',
        'fade-in': 'fade-in 0.4s ease-out both',
      },
    },
  },
  plugins: [typographyPlugin],
}
