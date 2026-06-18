import { Link } from 'react-router-dom'
import PrimaryButton from './PrimaryButton'
import { primarySurfaceClass } from '../../constants/themeClasses'

const cardClass =
  'flex flex-col rounded-card border border-dm-border bg-dm-card p-7 shadow-lg shadow-black/25 hover:scale-[1.02] hover:shadow-xl hover:border-dm-primary/30 transition-all duration-300'
const iconWrapClass =
  'mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-dm-primary/10'
const titleClass = 'text-lg font-bold text-dm-foreground'
const descClass = 'mt-2 flex-1 text-sm leading-relaxed text-dm-muted'
const buttonWrapClass = 'mt-6'
const buttonStyleClass =
  `${primarySurfaceClass} block w-full rounded-xl py-3 px-4 text-center font-medium transition-all duration-300 hover:shadow-lg hover:shadow-dm-primary/35 hover:brightness-110`

function ActionCard({ icon, title, description, buttonText, href, onClick, className = '' }) {
  return (
    <div className={[cardClass, className].filter(Boolean).join(' ')}>
      <div className={iconWrapClass}>{icon}</div>
      <h3 className={titleClass}>{title}</h3>
      <p className={descClass}>{description}</p>
      <div className={buttonWrapClass}>
        {href ? (
          <Link to={href} className={buttonStyleClass}>
            {buttonText}
          </Link>
        ) : (
          <PrimaryButton type="button" onClick={onClick}>
            {buttonText}
          </PrimaryButton>
        )}
      </div>
    </div>
  )
}

export default ActionCard
