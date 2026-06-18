import { User, Lock } from 'lucide-react'
import DocMindLogo from './DocMindLogo'

function UserIcon() {
  return <User size={20} className="text-current" />
}

function LockIcon() {
  return <Lock size={20} className="text-current" />
}

export { UserIcon, LockIcon }

function AuthHeader() {
  return (
    <header className="mb-8 text-center">
      <div className="inline-block">
        <DocMindLogo
          alt="DocMind"
          className="mx-auto h-48 w-auto object-contain animate-float-glow"
        />
      </div>
      <h1 className="mt-4 text-2xl font-bold tracking-tight text-dm-foreground">
        DocMind
      </h1>
      <p className="mt-1 text-sm text-dm-muted/70">
        Your AI study companion starts here.
      </p>
    </header>
  )
}

export default AuthHeader
