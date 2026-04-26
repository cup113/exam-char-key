export interface SelectionState {
  word: string
  context: string
  showTooltip: boolean
  x: number
  y: number
}

export interface QueryState {
  isOpen: boolean
  mode: 'quick' | 'deep'
  quickAnswer: string
  dictResult: string
  deepThink: string
  statusText: string
  loading: boolean
}

export interface SSEPayload {
  step?: 'quick_answer' | 'dictionary' | 'deep_think' | 'done'
  status?: string
  chunk?: string
  result?: string
  error?: string
}

export interface UserInfo {
  logged_in: boolean
  user_id?: string
  provider?: string
}
