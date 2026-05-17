import { apiClient } from './apiClient'
import type { ECHistoryEntry } from '@/types'

export async function migrateLegacyData(entries: ECHistoryEntry[]): Promise<void> {
  await apiClient.post('/api/migrate', { entries })
}
