import { apiClient } from './apiClient'

export interface HistoryRecord {
  id: number
  word: string
  context: string
  mode: string
  quick_answer: string
  dict_result: string
  deep_think: string
  created_at: string
}

export interface HistoryListResponse {
  records: HistoryRecord[]
}

export function listHistory(): Promise<HistoryListResponse> {
  return apiClient.get<HistoryListResponse>('/api/history')
}

export function createHistory(data: {
  word: string
  context: string
  mode: string
  quick_answer: string
  dict_result: string
  deep_think: string
}): Promise<void> {
  return apiClient.post('/api/history', data)
}

export function deleteHistory(id: number): Promise<void> {
  return apiClient.delete(`/api/history/${id}`)
}

export function batchDeleteHistory(ids: number[]): Promise<void> {
  return apiClient.post('/api/history/delete', { ids })
}
