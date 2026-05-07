import { useRef, useState, useCallback } from 'react'
import { FileUp } from 'lucide-react'
import PrimaryButton from './PrimaryButton'

const FILE_TYPES = ['PDF']
const ACCEPT = '.pdf'

const baseCardClass = [
  'flex flex-col items-center justify-center rounded-card border-2 border-dm-border',
  'bg-dm-card p-12 text-center shadow-xl md:p-16',
  'transition-all duration-300 ease-out cursor-pointer',
  'hover:scale-[1.02] hover:border-dm-primary/50 hover:shadow-2xl hover:shadow-dm-primary/10',
].join(' ')

const dragActiveClass =
  'scale-[1.02] !border-dm-primary !bg-dm-primary/5 shadow-2xl shadow-dm-primary/20'

function FileUploadPrompt({ onFileSelect, className = '' }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)
  const dragCounter = useRef(0)

  const handleClick = () => {
    if (onFileSelect) inputRef.current?.click()
  }

  const handleChange = (e) => {
    const file = e.target.files?.[0]
    if (file && onFileSelect) onFileSelect(file)
    e.target.value = ''
  }

  const handleDragEnter = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    dragCounter.current += 1
    setDragging(true)
  }, [])

  const handleDragLeave = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    dragCounter.current -= 1
    if (dragCounter.current === 0) setDragging(false)
  }, [])

  const handleDragOver = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
  }, [])

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault()
      e.stopPropagation()
      dragCounter.current = 0
      setDragging(false)
      const file = e.dataTransfer.files?.[0]
      if (file && onFileSelect) onFileSelect(file)
    },
    [onFileSelect],
  )

  const cardClasses = [baseCardClass, dragging && dragActiveClass, className]
    .filter(Boolean)
    .join(' ')

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT}
        className="sr-only"
        aria-hidden
        onChange={handleChange}
      />
      <div
        className={cardClasses}
        onClick={handleClick}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && handleClick()}
      >
        <div className="mb-6 animate-float">
          <FileUp size={72} className="text-dm-primary" strokeWidth={1.5} />
        </div>

        <p className="text-xl font-semibold text-dm-foreground md:text-2xl">
          {dragging ? 'Drop your file here' : 'Upload a file to start a new chat'}
        </p>

        <p className="mt-2 text-sm text-dm-muted">Drag & drop or click to browse</p>

        <div className="mt-5 flex items-center gap-2">
          {FILE_TYPES.map((type) => (
            <span
              key={type}
              className="rounded-lg bg-dm-border/60 px-3 py-1 text-xs font-medium text-dm-muted"
            >
              {type}
            </span>
          ))}
        </div>

        <div className="mt-8">
          <PrimaryButton
            type="button"
            onClick={(e) => {
              e.stopPropagation()
              handleClick()
            }}
            fullWidth={false}
            className="px-8 shadow-md shadow-dm-primary/25 transition-shadow duration-300 hover:shadow-lg hover:shadow-dm-primary/35"
          >
            Choose file
          </PrimaryButton>
        </div>
      </div>
    </>
  )
}

export default FileUploadPrompt
