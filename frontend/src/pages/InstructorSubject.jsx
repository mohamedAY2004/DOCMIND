import { useRef, useState, useCallback, useEffect, useMemo } from 'react'
import { useParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
import {
  Cloud,
  List,
  MessageCircle,
  Bot,
  FileText,
  LogOut,
  Trash2,
  Users,
  Loader2,
} from 'lucide-react'
import { AppLayout, AppTopBar } from '../components/layout'
import TestStudentBotModal from '../components/chat/TestStudentBotModal'
import PrimaryButton from '../components/ui/PrimaryButton'
import UploadZone from '../components/ui/UploadZone'
import PageFooter from '../components/ui/PageFooter'
import InstructorAvatarGroup from '../components/ui/InstructorAvatarGroup'
import useAuth from '../hooks/useAuth'
import {
  getSubjectById,
  getSubjectInstructors,
  getSubjectMaterials,
  deleteSubjectMaterial,
} from '../services/subjectService'
import { uploadMaterial } from '../services/uploadService'
import {
  getInstructorInitials,
  normalizeInstructorRow,
  titleCaseSlug,
} from '../utils/formatters'
import { fadeUp } from '../utils/motion'
import docmindLogo from '../assets/docmind-logo.png'

const cardClass = 'rounded-card border border-dm-border bg-dm-card p-8 shadow-xl'
const cardHeaderClass = 'flex items-center justify-between gap-2'
const cardTitleClass = 'text-lg font-bold text-dm-foreground'
const badgeProcessedClass =
  'shrink-0 rounded-full bg-dm-statusProcessed/90 px-2.5 py-0.5 text-xs font-medium text-dm-foreground'
const badgeIndexingClass =
  'shrink-0 rounded-full bg-dm-statusIndexing/90 px-2.5 py-0.5 text-xs font-medium text-dm-foreground'
const livePillClass = 'flex items-center gap-1.5 text-sm font-medium text-dm-primary'

const itemFade = {
  hidden: { opacity: 0, x: -12 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.3 } },
}

const INDEXING_POLL_MS = 4000
const MAX_FILE_BYTES = 50 * 1024 * 1024
const ALLOWED_EXTENSIONS = new Set(['.pdf'])

function InstructorSubject() {
  const { user, logout } = useAuth()
  const userId = user?.id ?? null
  const userRole = user?.role ?? null
  const { subjectId } = useParams()
  const fileInputRef = useRef(null)
  const [subject, setSubject] = useState(null)
  const [instructors, setInstructors] = useState([])
  const [materials, setMaterials] = useState([])
  const [testBotModalOpen, setTestBotModalOpen] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(null) // null = idle, 0-100 = uploading


  const subjectName = subject?.title || titleCaseSlug(subjectId)

  const coInstructors = useMemo(
    () => instructors.filter((i) => i.id !== userId),
    [instructors, userId],
  )
  const isAssigned = useMemo(
    () => (userId ? instructors.some((i) => i.id === userId) : false),
    [instructors, userId],
  )

  const refreshMaterials = useCallback(async () => {
    try {
      const list = await getSubjectMaterials(subjectId)
      setMaterials(Array.isArray(list) ? list : list?.items || [])
      return list
    } catch {
      toast.error('Could not load materials.')
      return []
    }
  }, [subjectId])

  useEffect(() => {
    let cancelled = false
    Promise.all([
      getSubjectById(subjectId).catch(() => null),
      getSubjectInstructors(subjectId).catch(() => []),
      // eslint-disable-next-line react-hooks/set-state-in-effect
      refreshMaterials(),
    ]).then(([subjectRes, instructorsRes]) => {
      if (cancelled) return
      setSubject(subjectRes)
      const raw = Array.isArray(instructorsRes)
        ? instructorsRes
        : instructorsRes?.items || []
      setInstructors(raw.map(normalizeInstructorRow).filter(Boolean))
    })
    return () => {
      cancelled = true
    }
  }, [subjectId, refreshMaterials])

  // Poll while any material is still indexing so the badge flips to
  // "Processed" once the server finishes embedding the document.
  useEffect(() => {
    const anyIndexing = materials.some((m) => m.status === 'indexing')
    if (!anyIndexing) return
    const t = setTimeout(() => {
      refreshMaterials()
    }, INDEXING_POLL_MS)
    return () => clearTimeout(t)
  }, [materials, refreshMaterials])

  const isUploading = uploadProgress !== null

  const handleBrowseFiles = useCallback(() => {
    if (isUploading) return // Prevent double-uploads
    fileInputRef.current?.click()
  }, [isUploading])

  const handleFileChange = useCallback(
    async (e) => {
      const file = e.target.files?.[0]
      e.target.value = ''
      if (!file) return

      const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase()
      if (!ALLOWED_EXTENSIONS.has(ext)) {
        toast.error('Only PDF files are supported.')
        return
      }
      if (file.size > MAX_FILE_BYTES) {
        toast.error('File is larger than the 50 MB limit.')
        return
      }

      const toastId = `upload-${Date.now()}`
      toast.loading(`Uploading ${file.name}…`, { id: toastId })
      setUploadProgress(0)

      try {
        const saved = await uploadMaterial(subjectId, file, {
          onUploadProgress: (progressEvent) => {
            const pct = progressEvent.total
              ? Math.round((progressEvent.loaded / progressEvent.total) * 100)
              : 0
            setUploadProgress(pct)
          },
        })
        setMaterials((prev) => [...prev, saved])
        toast.success(`Uploaded ${file.name}. Indexing…`, { id: toastId })
      } catch (err) {
        const code = err?.response?.data?.code
        let msg = 'Upload failed.'
        if (err?.code === 'ECONNABORTED' || err?.message?.includes('timeout')) {
          msg = 'Upload timed out. The file may be too large or the connection is slow.'
        } else if (!navigator.onLine) {
          msg = 'You appear to be offline. Check your connection and try again.'
        } else if (code === 'FILE_TOO_LARGE') {
          msg = 'File is larger than the 50 MiB limit.'
        } else if (code === 'UNSUPPORTED_MEDIA_TYPE') {
          msg = 'Only PDF files are supported.'
        } else if (code === 'CONFLICT') {
          msg = 'A material with this name already exists.'
        } else if (code === 'FILE_ENCRYPTED') {
          msg = 'Encrypted or password-protected PDFs cannot be processed. Please remove the password and try again.'
        } else if (err?.response?.data?.message) {
          msg = err.response.data.message
        }
        toast.error(msg, { id: toastId })
      } finally {
        setUploadProgress(null)
      }
    },
    [subjectId],
  )

  const handleDelete = useCallback(
    async (id) => {
      const target = materials.find((m) => m.id === id)
      try {
        await deleteSubjectMaterial(subjectId, id)
        setMaterials((prev) => prev.filter((m) => m.id !== id))
        if (target) toast('Removed ' + target.name)
      } catch {
        toast.error('Could not delete material.')
      }
    },
    [subjectId, materials],
  )

  return (
    <AppLayout
      scrollable
      topNav={
        <AppTopBar
          title="DocMind"
          logo={docmindLogo}
          logoHref="/instructor"
          logoClassName="h-14 w-auto object-contain"
          backTo="/instructor"
        >
          <button
            type="button"
            onClick={logout}
            className="ml-auto flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-dm-muted hover:bg-dm-background hover:text-dm-foreground transition-colors"
            aria-label="Log out"
          >
            <LogOut size={18} className="shrink-0 text-current" />
            Log out
          </button>
        </AppTopBar>
      }
    >
      <div className="mx-auto px-6 py-10 md:px-10 lg:py-12">
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          className="sr-only"
          aria-hidden
          onChange={handleFileChange}
        />

        <motion.section
          className="mb-10"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <h1 className="text-3xl font-bold text-dm-foreground md:text-4xl">{subjectName}</h1>
          <p className="mt-2 text-dm-muted">
            Manage course materials, lecture notes, and configure the AI assistant for this
            subject.
          </p>
        </motion.section>

        {instructors.length > 0 && (
          <motion.section
            className={`${cardClass} mb-8 !p-5 md:!p-6`}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35 }}
          >
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-full bg-dm-primary/15 text-dm-primary">
                  <Users size={18} />
                </span>
                <div>
                  <p className="text-sm font-semibold text-dm-foreground">
                    {instructors.length === 1
                      ? 'Sole instructor'
                      : `${instructors.length} instructors share this subject`}
                  </p>
                  <p className="text-xs text-dm-muted">
                    {coInstructors.length > 0
                      ? `You co-teach with ${coInstructors
                          .map((i) => i.name)
                          .join(', ')}. All uploads are shared.`
                      : 'You are currently the only instructor assigned.'}
                    {!isAssigned && userRole === 'instructor' && (
                      <span className="ml-1 text-amber-300">
                        You are not on this subject&apos;s roster.
                      </span>
                    )}
                  </p>
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <InstructorAvatarGroup
                  instructors={instructors}
                  highlightId={userId}
                  max={5}
                  size="md"
                />
                <ul className="flex flex-wrap gap-2">
                  {instructors.map((i) => {
                    const isSelf = i.id === userId
                    return (
                      <li
                        key={i.id}
                        className={[
                          'rounded-full border px-3 py-1 text-xs',
                          isSelf
                            ? 'border-dm-primary/50 bg-dm-primary/15 text-dm-foreground'
                            : 'border-dm-border bg-dm-background text-dm-muted',
                        ].join(' ')}
                      >
                        {i.name}
                        {isSelf && (
                          <span className="ml-1 text-dm-primary">(you)</span>
                        )}
                      </li>
                    )
                  })}
                </ul>
              </div>
            </div>
          </motion.section>
        )}

        <div className="flex flex-col gap-10">
          <div className="grid grid-cols-12 gap-10">
            <motion.section
              className={`${cardClass} col-span-12 lg:col-span-8`}
              variants={fadeUp}
              initial="hidden"
              animate="visible"
            >
              <div className={cardHeaderClass}>
                <div className="flex items-center gap-2">
                  <Cloud size={22} className="text-dm-primary" />
                  <h2 className={cardTitleClass}>Upload Materials</h2>
                </div>
                <span className="text-sm text-dm-muted">PDF only (Max 50MB)</span>
              </div>
              <div className="mt-6">
                <UploadZone
                  title={isUploading ? 'Uploading…' : 'Click or drag files to upload'}
                  hint="Uploads are shared with every instructor on this subject."
                  buttonText={isUploading ? `Uploading ${uploadProgress}%` : 'Browse Files'}
                  onBrowse={handleBrowseFiles}
                />
                {isUploading && (
                  <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-dm-border">
                    <div
                      className="h-full rounded-full bg-dm-primary transition-all duration-300 ease-out"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                )}
              </div>
            </motion.section>

            <motion.section
              className={`${cardClass} col-span-12 lg:col-span-4`}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.15, duration: 0.4 }}
            >
              <div className={cardHeaderClass}>
                <h2 className={cardTitleClass}>Bot Status</h2>
                <span className={livePillClass}>
                  <span className="h-2 w-2 rounded-full bg-dm-primary animate-pulse" aria-hidden />
                  Live
                </span>
              </div>
              <div className="mt-8 flex flex-col items-center">
                <div className="relative flex h-36 w-36 items-center justify-center">
                  <div
                    className="absolute inset-0 rounded-full border-4 border-dm-border"
                    aria-hidden
                  />
                  <motion.div
                    className="absolute inset-0 rounded-full border-4 border-transparent border-t-dm-primary"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 2, ease: 'linear', repeat: Infinity }}
                    aria-hidden
                  />
                  <div
                    className="absolute inset-4 rounded-full bg-dm-primary/5 shadow-[0_0_30px_rgba(13,110,115,0.25)]"
                    aria-hidden
                  />
                  <Bot size={44} className="relative text-dm-primary drop-shadow-[0_0_8px_rgba(13,110,115,0.5)]" />
                </div>
                <p className="mt-4 text-sm font-medium text-dm-foreground">Bot Ready</p>
                <PrimaryButton
                  type="button"
                  className="mt-6 flex w-full items-center justify-center gap-2"
                  onClick={() => setTestBotModalOpen(true)}
                >
                  <MessageCircle size={20} className="shrink-0" />
                  Test Student Bot
                </PrimaryButton>
              </div>
            </motion.section>
          </div>

          <motion.section
            className={cardClass}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25, duration: 0.4 }}
          >
            <div className={cardHeaderClass}>
              <div className="flex items-center gap-2">
                <List size={22} className="text-dm-primary" />
                <h2 className={cardTitleClass}>Uploaded Materials</h2>
                <span className="ml-1 rounded-full bg-dm-background px-2 py-0.5 text-xs font-medium text-dm-muted">
                  {materials.length}
                </span>
              </div>
              <span className="text-xs text-dm-muted">
                Shared across all instructors
              </span>
            </div>
            {materials.length === 0 ? (
              <p className="mt-6 rounded-xl border border-dashed border-dm-border bg-dm-background/40 px-4 py-8 text-center text-sm text-dm-muted">
                No materials uploaded yet. Be the first on the team to add one.
              </p>
            ) : (
              <ul className="mt-6 flex flex-col gap-3">
                <AnimatePresence mode="popLayout">
                  {materials.map((item) => {
                    const isSelf = item.uploadedById === userId
                    const initials =
                      item.uploadedByInitials ||
                      getInstructorInitials(item.uploadedByName)
                    return (
                      <motion.li
                        key={item.id}
                        variants={itemFade}
                        initial="hidden"
                        animate="visible"
                        exit={{ opacity: 0, x: 20, transition: { duration: 0.2 } }}
                        layout
                        className="flex items-center gap-4 rounded-xl border border-dm-border bg-dm-background/50 px-4 py-4 transition-colors hover:border-dm-border/80"
                      >
                        <FileText size={22} className="shrink-0 text-dm-muted" />
                        <div className="min-w-0 flex-1">
                          <p className="truncate font-medium text-dm-foreground">{item.name}</p>
                          <p className="mt-0.5 text-sm text-dm-muted">
                            {item.size} · {item.date}
                          </p>
                        </div>
                        <div className="hidden items-center gap-2 sm:flex">
                          <span
                            title={item.uploadedByName}
                            className={[
                              'flex h-7 w-7 items-center justify-center rounded-full text-[10px] font-semibold uppercase ring-2 ring-dm-card',
                              isSelf
                                ? 'bg-dm-primary/25 text-dm-primary ring-dm-primary/50'
                                : 'bg-dm-primary/15 text-dm-primary border border-dm-primary/30',
                            ].join(' ')}
                          >
                            {initials}
                          </span>
                          <span className="text-xs text-dm-muted">
                            {isSelf ? 'You' : item.uploadedByName}
                          </span>
                        </div>
                        <span
                          className={
                            item.status === 'processed' ? badgeProcessedClass : badgeIndexingClass
                          }
                        >
                          {item.status === 'processed' ? (
                            'Processed'
                          ) : (
                            <span className="flex items-center gap-1">
                              <Loader2 size={10} className="animate-spin" />
                              Indexing
                            </span>
                          )}
                        </span>
                        <button
                          type="button"
                          onClick={() => handleDelete(item.id)}
                          className="shrink-0 rounded-lg p-2 text-dm-muted hover:bg-dm-border hover:text-dm-foreground transition-colors"
                          aria-label={`Delete ${item.name}`}
                        >
                          <Trash2 size={20} />
                        </button>
                      </motion.li>
                    )
                  })}
                </AnimatePresence>
              </ul>
            )}
          </motion.section>
        </div>
      </div>

      <PageFooter />

      <TestStudentBotModal
        isOpen={testBotModalOpen}
        onClose={() => setTestBotModalOpen(false)}
        subjectName={subjectName}
        subjectId={subjectId}
      />
    </AppLayout>
  )
}

export default InstructorSubject
