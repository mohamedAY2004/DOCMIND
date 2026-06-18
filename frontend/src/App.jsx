import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'sonner'
import { ThemeProvider } from './hooks/useTheme'
import { AuthProvider } from './hooks/useAuth'
import { AppRoutes } from './routes'
import StudentAccessNavigationBridge from './components/StudentAccessNavigationBridge'

function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <AuthProvider>
          <StudentAccessNavigationBridge />
          <AppRoutes />
          <Toaster
            position="top-right"
            toastOptions={{
              className:
                '!bg-dm-card !border !border-dm-border !text-dm-foreground !shadow-xl',
              descriptionClassName: '!text-dm-muted',
            }}
            gap={8}
            richColors
          />
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  )
}

export default App
