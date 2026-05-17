import { describe, it, expect, vi } from 'vitest'

vi.mock('./apiClient')

import { apiClient } from './apiClient'
import { listHistory, createHistory, deleteHistory, batchDeleteHistory } from './historyService'

const mockApi = vi.mocked(apiClient)

describe('historyService', () => {
  it('listHistory calls get', async () => {
    mockApi.get.mockResolvedValue({ records: [] })
    const result = await listHistory()
    expect(mockApi.get).toHaveBeenCalledWith('/api/history')
    expect(result.records).toEqual([])
  })

  it('createHistory calls post with record data', async () => {
    const data = { word: '之', context: '', mode: 'quick', quick_answer: '', dict_result: '', deep_think: '' }
    mockApi.post.mockResolvedValue(undefined)
    await createHistory(data)
    expect(mockApi.post).toHaveBeenCalledWith('/api/history', data)
  })

  it('deleteHistory calls delete with record id', async () => {
    mockApi.delete.mockResolvedValue(undefined)
    await deleteHistory(5)
    expect(mockApi.delete).toHaveBeenCalledWith('/api/history/5')
  })

  it('batchDeleteHistory calls post with ids array', async () => {
    mockApi.post.mockResolvedValue(undefined)
    await batchDeleteHistory([1, 2, 3])
    expect(mockApi.post).toHaveBeenCalledWith('/api/history/delete', { ids: [1, 2, 3] })
  })
})
