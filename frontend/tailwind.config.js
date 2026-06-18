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
          background:      'rgb(var(--dm-background) / <alpha-value>)',
          card:            'rgb(var(--dm-card) / <alpha-value>)',
          primary:         'rgb(var(--dm-primary) / <alpha-value>)',
          'primary-hover': 'rgb(var(--dm-primary-hover) / <alpha-value>)',
          muted:           'rgb(var(--dm-muted) / <alpha-value>)',
          border:          'rgb(var(--dm-border) / <alpha-value>)',
          foreground:      'rgb(var(--dm-foreground) / <alpha-value>)',
          statusProcessed: 'rgb(var(--dm-status-processed) / <alpha-value>)',
          statusIndexing:  'rgb(var(--dm-status-indexing) / <alpha-value>)',
          onPrimary:       'rgb(var(--dm-on-primary) / <alpha-value>)',
        },
      },
      borderRadius: {
        'card': '24px',
      },
      typography: () => ({
        DEFAULT: {
          css: {
            '--tw-prose-body':          'rgb(var(--dm-foreground))',
            '--tw-prose-headings':      'rgb(var(--dm-foreground))',
            '--tw-prose-links':         'rgb(var(--dm-primary))',
            '--tw-prose-bold':          'rgb(var(--dm-foreground))',
            '--tw-prose-code':          'rgb(var(--dm-primary))',
            '--tw-prose-pre-bg':        'rgb(var(--dm-background))',
            '--tw-prose-pre-code':      'rgb(var(--dm-foreground))',
            '--tw-prose-quotes':        'rgb(var(--dm-muted))',
            '--tw-prose-quote-borders': 'rgb(var(--dm-primary))',
            '--tw-prose-counters':      'rgb(var(--dm-muted))',
            '--tw-prose-bullets':       'rgb(var(--dm-muted))',
            '--tw-prose-hr':            'rgb(var(--dm-border))',
            '--tw-prose-th-borders':    'rgb(var(--dm-border))',
            '--tw-prose-td-borders':    'rgb(var(--dm-border))',
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
          '0%, 100%': { filter: 'drop-shadow(0 0 6px var(--dm-glow-soft))' },
          '50%': { filter: 'drop-shadow(0 0 28px var(--dm-glow-strong))' },
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
