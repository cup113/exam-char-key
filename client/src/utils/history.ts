import type { ECHistoryEntry } from '@/types'

const LEGACY_STORAGE_KEY = 'EC_history'

export function detectLegacyData(): ECHistoryEntry[] | null {
  try {
    const raw = localStorage.getItem(LEGACY_STORAGE_KEY)
    if (raw) {
      const parsed = JSON.parse(raw)
      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed as ECHistoryEntry[]
      }
    }
  } catch {
    /* ignore */
  }
  return null
}

export function clearLegacyData(): void {
  localStorage.removeItem(LEGACY_STORAGE_KEY)
}
