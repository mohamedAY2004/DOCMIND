import { Link } from 'react-router-dom'

const cardClass = [
  'group flex flex-col rounded-card border border-dm-border bg-dm-card p-6 md:p-8',
  'shadow-lg shadow-black/20',
  'transition-all duration-300 ease-out',
  'hover:-translate-y-1 hover:shadow-xl hover:shadow-dm-primary/10 hover:border-dm-primary/40',
].join(' ')

const titleClass = 'text-lg font-bold text-dm-foreground'
const descClass = 'mt-2 flex-1 text-sm leading-relaxed text-dm-muted'
const buttonWrapClass = 'mt-6'

const buttonStyleClass = [
  'flex w-full items-center justify-center gap-2 rounded-xl py-3 px-4',
  'font-medium bg-dm-primary text-dm-foreground',
  'shadow-md shadow-dm-primary/20',
  'transition-all duration-300',
  'group-hover:shadow-lg group-hover:shadow-dm-primary/30 group-hover:scale-[1.02] group-hover:brightness-110',
].join(' ')

const arrowClass =
  'inline-block transition-transform duration-300 ease-out group-hover:translate-x-1'

function SubjectCard({
  title,
  description,
  buttonText = 'Start Chatting →',
  href,
  className = '',
}) {
  const hasArrow = buttonText.includes('→')
  const cleanText = hasArrow ? buttonText.replace('→', '').trim() : buttonText

  const buttonContent = (
    <>
      <span>{cleanText}</span>
      {hasArrow && <span className={arrowClass}>→</span>}
    </>
  )

  return (
    <div className={[cardClass, className].filter(Boolean).join(' ')}>
      <h3 className={titleClass}>{title}</h3>
      <p className={descClass}>{description}</p>
      <div className={buttonWrapClass}>
        {href ? (
          <Link to={href} className={buttonStyleClass}>
            {buttonContent}
          </Link>
        ) : (
          <span className={buttonStyleClass}>{buttonContent}</span>
        )}
      </div>
    </div>
  )
}

export default SubjectCard
