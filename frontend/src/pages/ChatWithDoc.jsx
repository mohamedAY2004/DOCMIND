import { useCallback, useEffect, useState } from 'react'
import { toast } from 'sonner'
import ChatScreen from '../components/chat/ChatScreen'
import useConversations from '../hooks/useConversations'
import {
  addDocFile,
  createDocConversation,
  deleteDocConversation,
  updateDocConversation,
  listDocConversations,
  listDocFiles,
  removeDocFile,
} from '../services/chatService'

const PROCESSING_POLL_MS = 3000
const MAX_FILES = 5

function humanizeUploadError(err, fallback = 'Upload failed.') {
  if (err?.code === 'ECONNABORTED' || err?.message?.includes('timeout'))
    return 'Upload timed out. The file may be too large or the connection is slow.'
  if (!navigator.onLine)
    return 'You appear to be offline. Check your connection and try again.'
  const code = err?.response?.data?.code
  if (code === 'FILE_TOO_LARGE') return 'File is larger than the 50 MiB limit.'
  if (code === 'UNSUPPORTED_MEDIA_TYPE')
    return 'Only PDF files are supported.'
  if (code === 'FILE_LIMIT' || code === 'MAX_FILES_EXCEEDED')
    return `Only ${MAX_FILES} documents can be attached to a conversation.`
  if (code === 'FILE_ENCRYPTED')
    return 'Encrypted or password-protected PDFs cannot be processed. Please remove the password and try again.'
  return err?.response?.data?.message || fallback
}

function ChatWithDoc() {
  const {
    conversations,
    activeId,
    loading: conversationsLoading,
    selectConversation,
    startNewConversation,
    prependConversation,
    updateConversation,
    deleteConversation,
    renameConversation,
  } = useConversations({
    fetcher: listDocConversations,
    remover: deleteDocConversation,
    updater: updateDocConversation,
  })

  const [files, setFiles] = useState([])
  const [uploadingFirstFileName, setUploadingFirstFileName] = useState('')

  // When the user switches to an existing conversation, fetch its files so
  // the attachment bar shows them. When they start a new chat (activeId
  // becomes null), clear the file tray unless an upload is mid-flight.
  useEffect(() => {
    if (!activeId) {
      setFiles((prev) => (uploadingFirstFileName ? prev : []))
      return
    }
    let cancelled = false
    listDocFiles(activeId)
      .then((data) => {
        if (cancelled) return
        const list = Array.isArray(data) ? data : data?.items || []
        setFiles(list)
      })
      .catch(() => {
        if (!cancelled) toast.error('Could not load this conversation’s files.')
      })
    return () => {
      cancelled = true
    }
    // Intentionally exclude `uploadingFirstFileName` — it only matters for
    // the null-activeId branch guard above.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeId])

  // Poll while any file in the active conversation is still indexing so
  // the attachment chip flips from spinner → icon without manual refresh.
  useEffect(() => {
    if (!activeId) return
    if (!files.some((f) => f.status === 'processing')) return
    let cancelled = false
    let timer = null
    const tick = async () => {
      try {
        const latest = await listDocFiles(activeId)
        if (cancelled) return
        const list = Array.isArray(latest) ? latest : latest?.items || []
        setFiles(list)
        if (list.every((f) => f.status !== 'processing')) {
          setUploadingFirstFileName('')
          return
        }
      } catch {
        /* transient */
      }
      if (!cancelled) timer = setTimeout(tick, PROCESSING_POLL_MS)
    }
    timer = setTimeout(tick, PROCESSING_POLL_MS)
    return () => {
      cancelled = true
      if (timer) clearTimeout(timer)
    }
  }, [activeId, files])

  const handleFirstUpload = useCallback(
    async (file) => {
      if (!file) return
      setUploadingFirstFileName(file.name)
      const toastId = `upload-first-${Date.now()}`
      toast.loading(`Uploading ${file.name}…`, { id: toastId })
      try {
        const conv = await createDocConversation([file])
        const id = conv?.id
        const list = Array.isArray(conv?.files) ? conv.files : []
        if (!id) throw new Error('missing-id')

        prependConversation({
          id,
          title: conv.title || file.name,
          updatedAt: conv.updatedAt,
        })
        setFiles(list)
        toast.success(`${file.name} received. Processing…`, { id: toastId })
      } catch (err) {
        toast.error(humanizeUploadError(err), { id: toastId })
        setUploadingFirstFileName('')
      }
    },
    [prependConversation],
  )

  const handleAddFile = useCallback(
    async (file) => {
      if (!activeId) return
      if (files.length >= MAX_FILES) {
        toast.error(`You can attach at most ${MAX_FILES} documents.`)
        return
      }
      const toastId = `upload-${Date.now()}`
      toast.loading(`Uploading ${file.name}…`, { id: toastId })
      try {
        const added = await addDocFile(activeId, file)
        setFiles((prev) => {
          if (prev.some((f) => f.id === added.id)) return prev
          return [...prev, added]
        })
        toast.success(`${file.name} uploaded. Processing…`, { id: toastId })
      } catch (err) {
        toast.error(humanizeUploadError(err), { id: toastId })
      }
    },
    [activeId, files.length],
  )

  const handleRemoveFile = useCallback(
    async (fileId) => {
      if (!activeId) return
      if (files.length <= 1) {
        toast.error('At least one document is required.')
        return
      }
      const removed = files.find((f) => f.id === fileId)
      const snapshot = files
      setFiles((prev) => prev.filter((f) => f.id !== fileId))
      try {
        await removeDocFile(activeId, fileId)
        if (removed) toast('Removed ' + removed.name)
      } catch {
        setFiles(snapshot)
        toast.error('Could not remove the file.')
      }
    },
    [activeId, files],
  )

  const handleNewChat = useCallback(() => {
    setFiles([])
    setUploadingFirstFileName('')
    startNewConversation()
  }, [startNewConversation])

  const handleSelectConversation = useCallback(
    (id) => {
      setUploadingFirstFileName('')
      selectConversation(id)
    },
    [selectConversation],
  )

  const handleDeleteConversation = useCallback(
    (id) => {
      if (id === activeId) {
        setFiles([])
        setUploadingFirstFileName('')
      }
      deleteConversation(id)
    },
    [activeId, deleteConversation],
  )

  // Keep the sidebar label fresh when the first message renames the chat.
  // If the server returns a renamed conversation later we just let the
  // list refetch on reload; this placeholder name is good enough for now.
  /* Removed auto-title logic as backend no longer replaces title
  useEffect(() => {
    if (!activeId || !uploadingFirstFileName) return
    const current = conversations.find((c) => c.id === activeId)
    if (current && !current.title) {
      updateConversation(activeId, { title: uploadingFirstFileName })
    }
  }, [activeId, uploadingFirstFileName, conversations, updateConversation])
  */

  return (
    <ChatScreen
      conversations={conversations}
      activeConversationId={activeId}
      onSelectConversation={handleSelectConversation}
      onNewChat={handleNewChat}
      onDeleteConversation={handleDeleteConversation}
      onRenameConversation={renameConversation}
      conversationsLoading={conversationsLoading}
      files={files}
      onFirstUpload={handleFirstUpload}
      onAddFile={handleAddFile}
      onRemoveFile={handleRemoveFile}
      uploadingFirstFileName={uploadingFirstFileName}
    />
  )
}

export default ChatWithDoc
