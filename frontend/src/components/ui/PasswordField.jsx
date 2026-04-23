import { useState } from 'react'
import { Eye, EyeOff } from 'lucide-react'
import InputField from './InputField'

function VisibilityToggle({ visible, onToggle }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className="hover:text-dm-foreground text-current"
      aria-label={visible ? 'Hide password' : 'Show password'}
    >
      {visible ? <EyeOff size={20} className="text-current" /> : <Eye size={20} className="text-current" />}
    </button>
  )
}

function PasswordField({ placeholder, icon, ...props }) {
  const [visible, setVisible] = useState(false)

  return (
    <InputField
      type={visible ? 'text' : 'password'}
      placeholder={placeholder}
      icon={icon}
      rightSlot={<VisibilityToggle visible={visible} onToggle={() => setVisible((v) => !v)} />}
      {...props}
    />
  )
}

export default PasswordField
