import { primaryButtonClass } from '../../constants/themeClasses'

function PrimaryButton({
  children,
  type = 'button',
  className = '',
  fullWidth = true,
  ...props
}) {
  return (
    <button
      type={type}
      className={[primaryButtonClass, fullWidth && 'w-full', className]
        .filter(Boolean)
        .join(' ')}
      {...props}
    >
      {children}
    </button>
  )
}

export default PrimaryButton
