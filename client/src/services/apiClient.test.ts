import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { apiClient, ApiError } from './apiClient'

describe('apiClient', () => {
  const mockFetch = vi.fn()

  beforeEach(() => {
    vi.stubGlobal('fetch', mockFetch)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    mockFetch.mockReset()
  })

  function mockResponse(overrides: Partial<Response> = {}): Response {
    return {
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
      headers: new Headers(),
      ...overrides,
    } as Response
  }

  describe('get', () => {
    it('calls GET with credentials and no content-type', async () => {
      mockFetch.mockResolvedValue(mockResponse())
      await apiClient.get('/api/test')
      expect(mockFetch).toHaveBeenCalledWith('/api/test', {
        method: 'GET',
        headers: {},
        credentials: 'include',
        body: undefined,
        signal: undefined,
      })
    })

    it('appends query params', async () => {
      mockFetch.mockResolvedValue(mockResponse())
      await apiClient.get('/api/test', { params: { a: '1', b: '2' } })
      const url = mockFetch.mock.calls[0]?.[0] as string
      expect(url).toContain('?a=1&b=2')
    })
  })

  describe('post', () => {
    it('calls POST with JSON body and content-type', async () => {
      mockFetch.mockResolvedValue(mockResponse())
      const body = { word: '之' }
      await apiClient.post('/api/test', body)
      expect(mockFetch).toHaveBeenCalledWith('/api/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(body),
        signal: undefined,
      })
    })

    it('calls POST without body and no content-type', async () => {
      mockFetch.mockResolvedValue(mockResponse())
      await apiClient.post('/api/test')
      expect(mockFetch).toHaveBeenCalledWith('/api/test', {
        method: 'POST',
        headers: {},
        credentials: 'include',
        body: undefined,
        signal: undefined,
      })
    })
  })

  describe('patch', () => {
    it('calls PATCH with JSON body', async () => {
      mockFetch.mockResolvedValue(mockResponse())
      await apiClient.patch('/api/test', { is_public: true })
      expect((mockFetch.mock.calls[0]?.[1] as RequestInit).method).toBe('PATCH')
    })
  })

  describe('delete', () => {
    it('calls DELETE', async () => {
      mockFetch.mockResolvedValue(mockResponse())
      await apiClient.delete('/api/test')
      expect((mockFetch.mock.calls[0]?.[1] as RequestInit).method).toBe('DELETE')
    })
  })

  describe('getRaw', () => {
    it('returns raw Response without parsing', async () => {
      const resp = mockResponse({ status: 500 })
      mockFetch.mockResolvedValue(resp)
      const result = await apiClient.getRaw('/api/test')
      expect(result).toBe(resp)
      // no json() call should happen
    })
  })

  describe('postRaw', () => {
    it('POSTs with JSON body and returns raw Response', async () => {
      const resp = mockResponse()
      mockFetch.mockResolvedValue(resp)
      const result = await apiClient.postRaw('/api/test', { key: 'val' })
      expect(result).toBe(resp)
      const opts = mockFetch.mock.calls[0]?.[1] as RequestInit
      expect(opts.method).toBe('POST')
      expect(opts.body).toBe(JSON.stringify({ key: 'val' }))
    })
  })

  describe('postForm', () => {
    it('POSTs with FormData and no content-type header', async () => {
      mockFetch.mockResolvedValue(mockResponse())
      const form = new FormData()
      form.append('file', 'test')
      await apiClient.postForm('/api/test', form)
      const opts = mockFetch.mock.calls[0]?.[1] as RequestInit
      expect(opts.method).toBe('POST')
      expect(opts.body).toBe(form)
      expect((opts.headers as Record<string, string>)?.['Content-Type']).toBeUndefined()
    })
  })

  describe('error handling', () => {
    it('throws ApiError with parsed detail on !resp.ok', async () => {
      mockFetch.mockResolvedValue(mockResponse({
        ok: false,
        status: 400,
        json: () => Promise.resolve({ detail: 'bad request' }),
      }))
      await expect(apiClient.get('/api/test')).rejects.toThrow(ApiError)
      await expect(apiClient.get('/api/test')).rejects.toThrow('bad request')
    })

    it('throws ApiError with status message when body is not JSON', async () => {
      mockFetch.mockResolvedValue(mockResponse({
        ok: false,
        status: 502,
        json: () => Promise.reject(new Error('not json')),
      }))
      try {
        await apiClient.get('/api/test')
      } catch (e) {
        expect(e).toBeInstanceOf(ApiError)
        expect((e as ApiError).status).toBe(502)
        expect((e as ApiError).detail).toBe('HTTP 502')
      }
    })

    it('has status and detail properties on ApiError', async () => {
      mockFetch.mockResolvedValue(mockResponse({
        ok: false,
        status: 429,
        json: () => Promise.resolve({ detail: 'rate limited' }),
      }))
      try {
        await apiClient.get('/api/test')
      } catch (e) {
        const err = e as ApiError
        expect(err.status).toBe(429)
        expect(err.detail).toBe('rate limited')
        expect(err.data).toEqual({ detail: 'rate limited' })
      }
    })
  })
})
