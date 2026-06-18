import docmindLogoLight from '../assets/docmind-logo.png'
import docmindLogoDark from '../assets/docmind_logo_dark.png'

export { docmindLogoLight, docmindLogoDark }

export function getDocMindLogoSrc(theme) {
  return theme === 'light' ? docmindLogoDark : docmindLogoLight
}
