import { getInstructorInitials } from '../../utils/formatters'

/**
 * Compact stack of instructor avatars for surfaces that need to show every
 * co-teacher assigned to a subject at a glance. Works on both the instructor
 * home cards and the admin subject list so the multi-instructor model is
 * consistently visible across roles.
 *
 * Props:
 * - instructors: Array<{ id, name }>
 * - max:        number — how many bubbles to show before collapsing into +N
 * - size:       'sm' | 'md'
 * - highlightId: string | null — draws a ring around the current user's
 *                 avatar so they can spot themselves in the list
 */
function InstructorAvatarGroup({
  instructors = [],
  max = 3,
  size = 'sm',
  highlightId = null,
  className = '',
}) {
  if (!instructors.length) return null

  const visible = instructors.slice(0, max)
  const overflow = instructors.length - visible.length

  const sizeClasses =
    size === 'md'
      ? 'h-9 w-9 text-xs'
      : 'h-7 w-7 text-[10px]'

  const ringOffset = 'ring-2 ring-dm-card'

  return (
    <div
      className={['flex -space-x-2', className].filter(Boolean).join(' ')}
      aria-label={`Instructors: ${instructors.map((i) => i.name).join(', ')}`}
    >
      {visible.map((instructor) => {
        const isSelf = instructor.id === highlightId
        return (
          <span
            key={instructor.id}
            title={instructor.name + (isSelf ? ' (you)' : '')}
            className={[
              'flex items-center justify-center rounded-full font-semibold uppercase',
              'bg-dm-primary/20 text-dm-primary border border-dm-primary/30',
              sizeClasses,
              ringOffset,
              isSelf ? 'ring-dm-primary' : '',
            ]
              .filter(Boolean)
              .join(' ')}
          >
            {getInstructorInitials(instructor.name)}
          </span>
        )
      })}
      {overflow > 0 && (
        <span
          title={instructors
            .slice(max)
            .map((i) => i.name)
            .join(', ')}
          className={[
            'flex items-center justify-center rounded-full font-semibold',
            'bg-dm-background text-dm-muted border border-dm-border',
            sizeClasses,
            ringOffset,
          ].join(' ')}
        >
          +{overflow}
        </span>
      )}
    </div>
  )
}

export default InstructorAvatarGroup
