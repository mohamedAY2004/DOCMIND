import useTheme from '../../hooks/useTheme'
import { getDocMindLogoSrc } from '../../constants/branding'

function DocMindLogo({ className = 'h-8 w-auto object-contain', alt = 'DocMind' }) {
  const { theme } = useTheme()

  return (
    <img
      src={getDocMindLogoSrc(theme)}
      alt={alt}
      className={className}
    />
  )
}

export default DocMindLogo
