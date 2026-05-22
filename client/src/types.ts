export interface TrackedWord {
  id: string
  word: string
  context: string
  offset: number
  mode: 'quick' | 'deep'
  status: 'pending' | 'loading' | 'done' | 'error'
  quickAnswer: string
  dictResult: string
  deepThink: string
  corpusEntries: CorpusEntry[]
  quickStatus: 'idle' | 'loading' | 'done' | 'error'
  corpusStatus: 'idle' | 'loading' | 'done' | 'error'
  dictStatus: 'idle' | 'loading' | 'done' | 'error'
  deepStatus: 'idle' | 'loading' | 'done' | 'error'
  startTime: number
  errorMessage?: string
}

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

export interface UserInfo {
  logged_in: boolean
  user_id?: string
  provider?: string
  is_admin?: boolean
}

export interface TrackedWordSnapshot {
  word: string
  context: string
  offset: number
  mode: 'quick' | 'deep'
  quickAnswer: string
  dictResult: string
  deepThink: string
  corpusEntries: CorpusEntry[]
}

export interface DocumentRecord {
  id: number
  user_id: string
  title: string
  source_text: string
  tracked_words: TrackedWordSnapshot[]
  is_public: boolean
  public_uuid: string | null
  created_at: string
  updated_at: string
}

export type TextSegment =
  | { type: 'text'; content: string }
  | { type: 'word'; word: TrackedWord }
