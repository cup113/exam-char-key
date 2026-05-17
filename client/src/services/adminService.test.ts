import { describe, it, expect, vi } from 'vitest'

vi.mock('./apiClient')

import { apiClient } from './apiClient'
import { importCorpus } from './adminService'

const mockApi = vi.mocked(apiClient)

describe('adminService', () => {
  it('calls postForm with file', async () => {
    const file = new File(['{"a":1}'], 'test.jsonl', { type: 'application/json' })
    const mockResp = { ok: true, json: () => Promise.resolve({ success: true, count: 10, filename: 'test.jsonl' }) } as Response
    mockApi.postForm.mockResolvedValue(mockResp)

    const result = await importCorpus(file)
    expect(mockApi.postForm).toHaveBeenCalledWith('/api/admin/import-corpus', expect.any(FormData))
    expect(result.success).toBe(true)
    expect(result.count).toBe(10)
  })

  it('returns permission error on 401/403', async () => {
    const file = new File([''], 'test.jsonl', { type: 'application/json' })
    const mockResp = { ok: false, status: 403 } as Response
    mockApi.postForm.mockResolvedValue(mockResp)

    const result = await importCorpus(file)
    expect(result.success).toBe(false)
    expect(result.error).toBe('无管理员权限')
  })

  it('returns text error on other failures', async () => {
    const file = new File([''], 'test.jsonl', { type: 'application/json' })
    const mockResp = { ok: false, status: 500, text: () => Promise.resolve('Internal Server Error') } as Response
    mockApi.postForm.mockResolvedValue(mockResp)

    const result = await importCorpus(file)
    expect(result.success).toBe(false)
    expect(result.error).toContain('Internal Server Error')
  })
})
