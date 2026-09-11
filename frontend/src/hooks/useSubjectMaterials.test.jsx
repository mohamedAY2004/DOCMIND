import { act, renderHook, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import useSubjectMaterials from './useSubjectMaterials'
import { getSubjectMaterials } from '../services/subjectService'
import { uploadMaterial } from '../services/uploadService'

vi.mock('../services/subjectService', () => ({ getSubjectMaterials: vi.fn(), deleteSubjectMaterial: vi.fn(), downloadSubjectMaterial: vi.fn() }))
vi.mock('../services/uploadService', () => ({ uploadMaterial: vi.fn() }))
afterEach(() => vi.resetAllMocks())

describe('subject material ownership', () => {
  it('rejects delayed reads, upload progress and upload results after a subject change', async () => {
    let finishRead
    let finishUpload
    let progress
    getSubjectMaterials.mockImplementation((id) => id === 'a'
      ? new Promise((resolve) => { finishRead = resolve }) : Promise.resolve([{ id: 'new', status: 'processed' }]))
    uploadMaterial.mockImplementation((_id, _file, options) => {
      progress = options.onUploadProgress
      return new Promise((resolve) => { finishUpload = resolve })
    })
    const { result, rerender } = renderHook(({ id }) => useSubjectMaterials(id), { initialProps: { id: 'a' } })
    act(() => { void result.current.upload(new File(['pdf'], 'lecture.pdf')) })
    rerender({ id: 'b' })
    await waitFor(() => expect(result.current.materials[0]?.id).toBe('new'))
    await act(async () => {
      finishRead([{ id: 'old' }]); progress({ loaded: 10, total: 20 }); finishUpload({ id: 'old-upload' })
    })
    expect(result.current.materials).toEqual([{ id: 'new', status: 'processed' }])
    expect(result.current.uploadProgress).toBeNull()
  })
})
