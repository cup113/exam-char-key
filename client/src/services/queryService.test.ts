import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('./apiClient', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
    getRaw: vi.fn(),
    postRaw: vi.fn(),
    postForm: vi.fn(),
  },
  ApiError: class ApiError extends Error {
    constructor(status: number, detail: string, data?: unknown) {
      super(detail)
      this.name = 'ApiError'
      this.status = status
      this.detail = detail
      this.data = data
    }
    status: number
    detail: string
    data?: unknown
  },
}))
vi.mock('@/utils/sse')

import { apiClient } from './apiClient'
import { readSSEStream } from '@/utils/sse'
import { queryQuick, queryCorpus, queryDictionary, queryDeep } from './queryService'

const mockApi = vi.mocked(apiClient)
const mockReadSSE = vi.mocked(readSSEStream)

function okResponse(body?: unknown): Response {
  return {
    ok: true,
    status: 200,
    json: () => Promise.resolve(body ?? {}),
    headers: new Headers(),
  } as Response
}

function errResponse(status: number, detail?: string): Response {
  return {
    ok: false,
    status,
    json: () => Promise.resolve(detail ? { detail } : {}),
  } as Response
}

describe('queryService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('queryQuick', () => {
    it('calls getRaw and reads SSE stream', async () => {
      const onChunk = vi.fn()
      mockApi.getRaw.mockResolvedValue(okResponse())
      await queryQuick('之', '之乎者也', new AbortController().signal, onChunk)
      expect(mockApi.getRaw).toHaveBeenCalledWith('/api/query/quick', {
        params: { word: '之', context: '之乎者也' },
        signal: expect.any(AbortSignal),
      })
      expect(mockReadSSE).toHaveBeenCalled()
    })

    it('throws on non-ok response', async () => {
      mockApi.getRaw.mockResolvedValue(errResponse(500, 'quick failed'))
      await expect(queryQuick('之', '', new AbortController().signal, vi.fn())).rejects.toThrow('quick failed')
    })
  })

  describe('queryCorpus', () => {
    it('returns entries from JSON response', async () => {
      mockApi.getRaw.mockResolvedValue(okResponse({ entries: [{ id: 1, type: 'classical', context: '', word: '之', answer: '' }] }))
      const entries = await queryCorpus('之', new AbortController().signal)
      expect(entries).toHaveLength(1)
      expect(entries[0]?.id).toBe(1)
    })

    it('throws on error with fallback message', async () => {
      mockApi.getRaw.mockResolvedValue(errResponse(502))
      await expect(queryCorpus('之', new AbortController().signal)).rejects.toThrow('语料库查询失败')
    })
  })

  describe('queryDictionary', () => {
    it('returns result string from JSON response', async () => {
      mockApi.getRaw.mockResolvedValue(okResponse({ result: '{"basic":[]}' }))
      const result = await queryDictionary('之', new AbortController().signal)
      expect(result).toBe('{"basic":[]}')
    })
  })

  describe('queryDeep', () => {
    it('calls getRaw with deep endpoint and reads SSE', async () => {
      const onChunk = vi.fn()
      mockApi.getRaw.mockResolvedValue(okResponse())
      await queryDeep('之', 'context', new AbortController().signal, onChunk)
      expect(mockApi.getRaw).toHaveBeenCalledWith('/api/query/deep', {
        params: { word: '之', context: 'context' },
        signal: expect.any(AbortSignal),
      })
    })
  })
})
