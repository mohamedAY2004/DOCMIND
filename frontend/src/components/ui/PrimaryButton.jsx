const buttonClass =
  'rounded-xl font-medium py-3 px-4 bg-dm-primary text-dm-foreground transition-all duration-200 hover:opacity-95 focus:outline-none focus:ring-2 focus:ring-dm-primary focus:ring-offset-2 focus:ring-offset-dm-card'

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
      className={[buttonClass, fullWidth && 'w-full', className]
        .filter(Boolean)
        .join(' ')}
      {...props}
    >
      {children}
    </button>
  )
}

export default PrimaryButton
