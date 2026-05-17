import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

vi.mock('./apiClient')
vi.mock('@/utils/download')

import { apiClient } from './apiClient'
import { downloadBlob } from '@/utils/download'
import { exportRecords } from './exportService'

const mockApi = vi.mocked(apiClient)
const mockDownloadBlob = vi.mocked(downloadBlob)

describe('exportService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('calls postRaw with format and ids', async () => {
    const blob = new Blob(['test'])
    mockApi.postRaw.mockResolvedValue({
      ok: true,
      blob: () => Promise.resolve(blob),
      headers: new Headers({ 'Content-Disposition': 'attachment; filename="records.json"' }),
    } as Response)

    await exportRecords('json', [1, 2])
    expect(mockApi.postRaw).toHaveBeenCalledWith('/api/export', { format: 'json', ids: [1, 2] })
  })

  it('calls postRaw without ids for all export', async () => {
    const blob = new Blob(['test'])
    mockApi.postRaw.mockResolvedValue({
      ok: true,
      blob: () => Promise.resolve(blob),
      headers: new Headers({ 'Content-Disposition': 'attachment; filename="all.json"' }),
    } as Response)

    await exportRecords('json')
    expect(mockApi.postRaw).toHaveBeenCalledWith('/api/export', { format: 'json' })
  })

  it('downloads the blob with parsed filename', async () => {
    const blob = new Blob(['{"data":"test"}'])
    mockApi.postRaw.mockResolvedValue({
      ok: true,
      blob: () => Promise.resolve(blob),
      headers: new Headers({ 'Content-Disposition': 'attachment; filename="study_records.json"' }),
    } as Response)

    await exportRecords('json')
    expect(mockDownloadBlob).toHaveBeenCalledWith(blob, 'study_records.json')
  })

  it('uses fallback filename when Content-Disposition is missing', async () => {
    const blob = new Blob(['test'])
    mockApi.postRaw.mockResolvedValue({
      ok: true,
      blob: () => Promise.resolve(blob),
      headers: new Headers(),
    } as Response)

    await exportRecords('word')
    expect(mockDownloadBlob).toHaveBeenCalledWith(blob, '学习记录.docx')
  })

  it('throws on non-ok response', async () => {
    mockApi.postRaw.mockResolvedValue({
      ok: false,
      json: () => Promise.resolve({ detail: 'server error' }),
    } as Response)

    await expect(exportRecords('json')).rejects.toThrow('server error')
  })
})
