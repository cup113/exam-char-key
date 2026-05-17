import { apiClient } from './apiClient'

export interface ImportResult {
  success: boolean
  count?: number
  filename?: string
  error?: string
}

export async function importCorpus(file: File): Promise<ImportResult> {
  const form = new FormData()
  form.append('file', file)

  const resp = await apiClient.postForm('/api/admin/import-corpus', form)

  if (resp.ok) {
    return resp.json() as Promise<ImportResult>
  }

  if (resp.status === 401 || resp.status === 403) {
    return { success: false, error: '无管理员权限' }
  }

  const text = await resp.text()
  return { success: false, error: text || `请求失败 (${resp.status})` }
}
