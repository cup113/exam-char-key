import { describe, it, expect, vi } from 'vitest'

vi.mock('./apiClient')

import { apiClient } from './apiClient'
import { listDocs, createDoc, deleteDoc, updateDoc, getPublicDoc } from './documentService'

const mockApi = vi.mocked(apiClient)

describe('documentService', () => {
  it('listDocs calls get with pagination params', async () => {
    mockApi.get.mockResolvedValue({ documents: [] })
    await listDocs(10, 5)
    expect(mockApi.get).toHaveBeenCalledWith('/api/documents', {
      params: { limit: '10', offset: '5' },
    })
  })

  it('listDocs uses default pagination', async () => {
    mockApi.get.mockResolvedValue({ documents: [] })
    await listDocs()
    expect(mockApi.get).toHaveBeenCalledWith('/api/documents', {
      params: { limit: '50', offset: '0' },
    })
  })

  it('createDoc calls post with document data', async () => {
    const data = { title: 'test', source_text: 'abc', tracked_words: [], is_public: false }
    mockApi.post.mockResolvedValue({ id: 1, ...data })
    const result = await createDoc(data)
    expect(mockApi.post).toHaveBeenCalledWith('/api/documents', data)
    expect(result.id).toBe(1)
  })

  it('deleteDoc calls delete with document id', async () => {
    mockApi.delete.mockResolvedValue(undefined)
    await deleteDoc(42)
    expect(mockApi.delete).toHaveBeenCalledWith('/api/documents/42')
  })

  it('updateDoc calls patch with is_public', async () => {
    mockApi.patch.mockResolvedValue(undefined)
    await updateDoc(1, { is_public: true })
    expect(mockApi.patch).toHaveBeenCalledWith('/api/documents/1', { is_public: true })
  })

  it('getPublicDoc calls get with document uuid', async () => {
    mockApi.get.mockResolvedValue({ id: 1, public_uuid: 'xxx' })
    const result = await getPublicDoc('xxx')
    expect(mockApi.get).toHaveBeenCalledWith('/api/documents/public/xxx')
    expect(result.public_uuid).toBe('xxx')
  })
})
