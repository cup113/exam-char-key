import { describe, it, expect, vi } from 'vitest'

vi.mock('./apiClient')

import { apiClient } from './apiClient'
import { migrateLegacyData } from './migrateService'

const mockApi = vi.mocked(apiClient)

describe('migrateService', () => {
  it('calls post with entries', async () => {
    const entries = [{ id: '1', level: '1', front: '之', back: '代词', additions: [], createdAt: '' }]
    mockApi.post.mockResolvedValue(undefined)
    await migrateLegacyData(entries)
    expect(mockApi.post).toHaveBeenCalledWith('/api/migrate', { entries })
  })
})
