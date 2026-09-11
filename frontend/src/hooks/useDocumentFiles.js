import { useCallback, useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'
import { addDocFile, createDocConversation, listDocFiles, removeDocFile } from '../services/chatService'
import useRequestScope from './useRequestScope'

const MAX_FILES = 5

export default function useDocumentFiles(conversationId, onCreated) {
  const [files, setFiles] = useState([])
  const [uploadingFirstFileName, setUploadingFirstFileName] = useState('')
  const { capture, reset: resetScope } = useRequestScope(conversationId)
  const reading = useRef(0)
  const uploading = useRef(false)

  const refresh = useCallback(async () => {
    if (!conversationId) return
    const owner = capture()
    const request = ++reading.current
    try {
      const items = await listDocFiles(conversationId, { signal: owner.signal })
      if (!owner.owns() || reading.current !== request) return
      setFiles(items)
      if (items.every((file) => file.status !== 'processing')) setUploadingFirstFileName('')
    } catch (error) {
      if (owner.owns() && reading.current === request) {
        toast.error(error.message || 'Could not load files.')
        setFiles((previous) => [...previous])
      }
    }
  }, [conversationId, capture])

  useEffect(() => {
    setFiles([])
    setUploadingFirstFileName('')
    uploading.current = false
    void refresh()
  }, [refresh])

  useEffect(() => {
    if (!files.some((file) => file.status === 'processing')) return
    const timer = setTimeout(refresh, 3000)
    return () => clearTimeout(timer)
  }, [files, refresh])

  const upload = useCallback(async (file) => {
    if (!file || uploading.current) return
    if (conversationId && files.length >= MAX_FILES) {
      toast.error(`You can attach at most ${MAX_FILES} documents.`)
      return
    }
    const owner = capture()
    uploading.current = true
    if (!conversationId) setUploadingFirstFileName(file.name)
    try {
      if (conversationId) {
        const added = await addDocFile(conversationId, file, { signal: owner.signal })
        if (!owner.owns()) return
        reading.current += 1
        setFiles((previous) => [...previous.filter((item) => item.id !== added.id), added])
      } else {
        const conversation = await createDocConversation([file], { signal: owner.signal })
        if (!owner.owns()) return
        if (!conversation?.id) throw new Error('The server returned an invalid conversation.')
        onCreated(conversation)
        setFiles(conversation.files)
      }
      toast.success(`${file.name} received. Processing…`)
    } catch (error) {
      if (owner.owns()) {
        toast.error(error?.response?.data?.message || 'Upload failed. Please try again.')
        setUploadingFirstFileName('')
      }
    } finally { if (owner.owns()) uploading.current = false }
  }, [conversationId, files.length, capture, onCreated])

  const remove = useCallback(async (id) => {
    if (!conversationId) return
    if (files.length <= 1) { toast.error('At least one document is required.'); return }
    const owner = capture()
    try {
      await removeDocFile(conversationId, id, { signal: owner.signal })
      if (!owner.owns()) return
      reading.current += 1
      setFiles((previous) => previous.filter((file) => file.id !== id))
    } catch (error) { if (owner.owns()) toast.error(error?.response?.data?.message || 'Could not remove the file.') }
  }, [conversationId, files.length, capture])

  return { files, uploadingFirstFileName, upload, remove,
    reset: () => { resetScope(); setFiles([]); setUploadingFirstFileName(''); uploading.current = false } }
}
