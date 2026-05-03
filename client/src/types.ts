export interface SelectionState {
  word: string
  context: string
  showTooltip: boolean
  x: number
  y: number
}

export interface CorpusEntry {
  id: number
  type: string
  context: string
  word: string
  answer: string
}

export interface ECHistoryEntry {
  id: string
  level: string
  front: string
  back: string
  additions: string[]
  createdAt: string
}

export interface ExportResponse {
  docx_filename?: string
  apkg_filename?: string
}

import type { TrackedWord } from '@/stores/words'

export interface UserInfo {
  logged_in: boolean
  user_id?: string
  provider?: string
}

export type TextSegment =
  | { type: 'text'; content: string }
  | { type: 'word'; word: TrackedWord }
