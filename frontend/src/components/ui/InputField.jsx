const wrapperClass =
  'group relative flex items-center rounded-lg bg-dm-background border border-dm-border transition-all duration-200 focus-within:border-dm-primary/50 focus-within:ring-2 focus-within:ring-dm-primary/20 focus-within:shadow-md focus-within:shadow-dm-primary/5'
const inputCoreClass =
  'w-full rounded-lg border-0 bg-transparent text-dm-foreground placeholder:text-dm-foreground/60 transition-colors duration-200 focus:outline-none'
const pl = (hasIcon) => (hasIcon ? 'pl-12' : 'pl-4')
const pr = (hasRight) => (hasRight ? 'pr-12' : 'pr-4')

function InputField({
  placeholder,
  icon,
  rightSlot,
  type = 'text',
  className = '',
  compact = false,
  ...props
}) {
  const inputClass = `${inputCoreClass} ${compact ? 'py-2 text-sm' : 'py-3'} ${pl(!!icon)} ${pr(!!rightSlot)}`

  return (
    <div className={[wrapperClass, className].filter(Boolean).join(' ')}>
      {icon && (
        <span className="pointer-events-none absolute left-4 flex text-dm-foreground/80 transition-colors duration-200 group-focus-within:text-dm-primary">
          {icon}
        </span>
      )}
      <input
        type={type}
        placeholder={placeholder}
        className={inputClass}
        {...props}
      />
      {rightSlot && (
        <span className="absolute right-4 flex text-dm-foreground/80 transition-colors duration-200 group-focus-within:text-dm-primary">
          {rightSlot}
        </span>
      )}
    </div>
  )
}

export default InputField
