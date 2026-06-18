import { AlertCircle, RefreshCw } from 'lucide-react'

const bannerClass =
  'shrink-0 flex items-center gap-3 border-t border-red-500/20 bg-red-500/5 px-4 py-2.5'

function ErrorBanner({ message, onRetry, onDismiss, icon = false }) {
  return (
    <div className={bannerClass}>
      {icon && <AlertCircle size={16} className="shrink-0 text-red-400" />}
      <p className="flex-1 text-sm text-red-400">
        {message || 'Something went wrong. Please try again.'}
      </p>
      <div className="flex items-center gap-2">
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="flex items-center gap-1.5 rounded-md bg-red-500/10 px-3 py-1.5 text-sm font-medium text-red-400 hover:bg-red-500/20 transition-colors"
          >
            <RefreshCw size={14} />
            Retry
          </button>
        )}
        {onDismiss && (
          <button
            type="button"
            onClick={onDismiss}
            className="text-sm font-medium text-red-400 hover:text-red-300 transition-colors"
          >
            Dismiss
          </button>
        )}
      </div>
    </div>
  )
}

export default ErrorBanner
