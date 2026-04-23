import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'sonner'
import { AuthProvider } from './hooks/useAuth'
import { AppRoutes } from './routes'
import StudentAccessNavigationBridge from './components/StudentAccessNavigationBridge'

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <StudentAccessNavigationBridge />
        <AppRoutes />
        <Toaster
          position="top-right"
          toastOptions={{
            className:
              '!bg-dm-card !border !border-dm-border !text-dm-foreground !shadow-xl !shadow-black/20',
            descriptionClassName: '!text-dm-muted',
          }}
          gap={8}
          richColors
        />
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
