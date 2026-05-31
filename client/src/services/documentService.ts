import { apiClient } from './apiClient'
import type { DocumentRecord } from '@/types'

export interface DocListItem {
  id: number
  user_id: string
  title: string
  source_text: string
  tracked_words: unknown[]
  is_public: boolean
  public_uuid: string | null
  created_at: string
}

export interface DocListResponse {
  documents: DocListItem[]
}

export function listDocs(limit = 50, offset = 0): Promise<DocListResponse> {
  return apiClient.get<DocListResponse>('/api/documents', {
    params: { limit: String(limit), offset: String(offset) },
  })
}

export function createDoc(data: {
  title: string
  source_text: string
  tracked_words: unknown[]
  is_public: boolean
}): Promise<DocumentRecord> {
  return apiClient.post<DocumentRecord>('/api/documents', data)
}

export function deleteDoc(id: number): Promise<void> {
  return apiClient.delete(`/api/documents/${id}`)
}

export function updateDoc(
  id: number,
  data: {
    title?: string
    is_public?: boolean
    source_text?: string
    tracked_words?: unknown[]
  },
): Promise<void> {
  return apiClient.patch(`/api/documents/${id}`, data)
}

export function getPublicDoc(uuid: string): Promise<DocumentRecord> {
  return apiClient.get<DocumentRecord>(`/api/documents/public/${uuid}`)
}
