import { apiClient } from './apiClient'
import { downloadBlob } from '@/utils/download'

const FORMAT_EXTENSIONS: Record<string, string> = {
  json: 'json',
  word: 'docx',
  apkg: 'apkg',
}

function parseFilename(disposition: string, format: string): string {
  const match = disposition.match(/filename="?(.+?)"?$/)
  return match?.[1] ?? `学习记录.${FORMAT_EXTENSIONS[format] || format}`
}

export async function exportRecords(
  format: 'json' | 'word' | 'apkg',
  ids?: number[],
): Promise<void> {
  const body: Record<string, unknown> = { format }
  if (ids && ids.length > 0) body.ids = ids

  const postResp = await apiClient.postRaw('/api/export', body)

  if (!postResp.ok) {
    let detail = '导出失败'
    try {
      const err = await postResp.json()
      if (err.detail) detail = err.detail
    } catch { /* ignore */ }
    throw new Error(detail)
  }

  const blob = await postResp.blob()
  const disposition = postResp.headers.get('Content-Disposition') || ''
  const filename = parseFilename(disposition, format)
  downloadBlob(blob, filename)
}
