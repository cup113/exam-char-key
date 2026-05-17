export class ApiError extends Error {
  status: number
  detail: string
  data?: unknown

  constructor(status: number, detail: string, data?: unknown) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
    this.data = data
  }
}

interface RequestOptions {
  params?: Record<string, string>
  signal?: AbortSignal
}

class ApiClient {
  async get<T = unknown>(path: string, opts?: RequestOptions): Promise<T> {
    return this.request<T>(path, { ...opts, method: 'GET' })
  }

  post<T = unknown>(path: string, body?: unknown, opts?: RequestOptions): Promise<T> {
    return this.request<T>(path, {
      ...opts,
      method: 'POST',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  }

  patch<T = unknown>(path: string, body?: unknown, opts?: RequestOptions): Promise<T> {
    return this.request<T>(path, {
      ...opts,
      method: 'PATCH',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  }

  delete<T = unknown>(path: string, opts?: RequestOptions): Promise<T> {
    return this.request<T>(path, { ...opts, method: 'DELETE' })
  }

  async getRaw(path: string, opts?: RequestOptions): Promise<Response> {
    const url = this.buildUrl(path, opts?.params)
    return fetch(url, { credentials: 'include', signal: opts?.signal })
  }

  async postRaw(path: string, body?: unknown, opts?: RequestOptions): Promise<Response> {
    const url = this.buildUrl(path, opts?.params)
    const headers: Record<string, string> = {}
    if (body !== undefined) {
      headers['Content-Type'] = 'application/json'
    }
    return fetch(url, {
      method: 'POST',
      headers,
      credentials: 'include',
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: opts?.signal,
    })
  }

  async postForm(path: string, formData: FormData, opts?: RequestOptions): Promise<Response> {
    const url = this.buildUrl(path, opts?.params)
    return fetch(url, {
      method: 'POST',
      credentials: 'include',
      body: formData,
      signal: opts?.signal,
    })
  }

  private async request<T>(path: string, init: RequestInit & RequestOptions): Promise<T> {
    const { params, signal, method, body } = init
    const url = this.buildUrl(path, params)

    const headers: Record<string, string> = {}
    if (body && typeof body === 'string') {
      headers['Content-Type'] = 'application/json'
    }

    const resp = await fetch(url, {
      method,
      headers,
      credentials: 'include',
      body,
      signal,
    })

    if (!resp.ok) {
      let detail = `HTTP ${resp.status}`
      let data: unknown
      try {
        data = await resp.json()
        detail = (data as any)?.detail || detail
      } catch {
        // response body not JSON
      }
      throw new ApiError(resp.status, detail, data)
    }

    return resp.json() as Promise<T>
  }

  private buildUrl(path: string, params?: Record<string, string>): string {
    let url = path
    if (params) {
      const qs = new URLSearchParams(params).toString()
      url += `?${qs}`
    }
    return url
  }
}

export const apiClient = new ApiClient()
