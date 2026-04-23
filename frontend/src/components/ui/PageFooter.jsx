const footerClass =
  'mt-auto shrink-0 border-t border-dm-border/50 py-3 text-center text-xs text-dm-muted/60'

function PageFooter({ className = '', children = '© 2026 DocMind. All rights reserved.' }) {
  return <footer className={[footerClass, className].filter(Boolean).join(' ')}>{children}</footer>
}

export default PageFooter
