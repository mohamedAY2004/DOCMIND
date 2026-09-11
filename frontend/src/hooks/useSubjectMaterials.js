import { useCallback, useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'
import { deleteSubjectMaterial, downloadSubjectMaterial, getSubjectMaterials } from '../services/subjectService'
import { uploadMaterial } from '../services/uploadService'
import useRequestScope from './useRequestScope'

export default function useSubjectMaterials(subjectId) {
  const [materials, setMaterials] = useState([])
  const [uploadProgress, setUploadProgress] = useState(null)
  const [downloadingId, setDownloadingId] = useState(null)
  const { capture } = useRequestScope(subjectId)
  const read = useRef(0)
  const uploading = useRef(false)

  const refresh = useCallback(async () => {
    const owner = capture()
    const id = ++read.current
    try {
      const items = await getSubjectMaterials(subjectId, { signal: owner.signal })
      if (owner.owns() && read.current === id) setMaterials(items)
    } catch {
      if (owner.owns() && read.current === id) {
        toast.error('Could not load materials.')
        setMaterials((previous) => [...previous])
      }
    }
  }, [subjectId, capture])

  useEffect(() => {
    setMaterials([])
    setUploadProgress(null)
    setDownloadingId(null)
    uploading.current = false
    void refresh()
  }, [refresh])

  useEffect(() => {
    if (!materials.some((material) => material.status === 'indexing')) return
    const timer = setTimeout(refresh, 4000)
    return () => clearTimeout(timer)
  }, [materials, refresh])

  const upload = useCallback(async (file) => {
    if (!file || uploading.current) return
    if (!file.name.toLowerCase().endsWith('.pdf')) { toast.error('Only PDF files are supported.'); return }
    if (file.size > 50 * 1024 * 1024) { toast.error('File is larger than the 50 MiB limit.'); return }
    const owner = capture()
    uploading.current = true
    setUploadProgress(0)
    try {
      const saved = await uploadMaterial(subjectId, file, {
        signal: owner.signal,
        onUploadProgress: ({ loaded, total }) => {
          if (owner.owns()) setUploadProgress(total ? Math.round(loaded / total * 100) : 0)
        },
      })
      if (!owner.owns()) return
      // An earlier poll cannot replace the upload result.
      read.current += 1
      setMaterials((previous) => [...previous.filter((material) => material.id !== saved.id), saved])
      toast.success(`Uploaded ${file.name}. Indexing…`)
    } catch (error) {
      if (owner.owns()) toast.error(error?.response?.data?.message || 'Upload failed. Please try again.')
    } finally {
      if (owner.owns()) { uploading.current = false; setUploadProgress(null) }
    }
  }, [subjectId, capture])

  const remove = useCallback(async (id) => {
    const owner = capture()
    try {
      await deleteSubjectMaterial(subjectId, id, { signal: owner.signal })
      if (!owner.owns()) return
      read.current += 1
      setMaterials((previous) => previous.filter((material) => material.id !== id))
      toast.success('Material removed.')
    } catch {
      if (owner.owns()) toast.error('Could not delete material.')
    }
  }, [subjectId, capture])

  const download = useCallback(async (item) => {
    const owner = capture()
    setDownloadingId(item.id)
    try { await downloadSubjectMaterial(subjectId, item.id, item.name, { signal: owner.signal }) }
    catch { if (owner.owns()) toast.error('Could not download this material.') }
    finally { if (owner.owns()) setDownloadingId((id) => id === item.id ? null : id) }
  }, [subjectId, capture])

  return { materials, uploadProgress, downloadingId, refresh, upload, remove, download }
}
