import type { TrackedWord, TrackedWordSnapshot } from '@/types'

export function toSnapshot(w: TrackedWord): TrackedWordSnapshot {
  return {
    word: w.word,
    context: w.context,
    offset: w.offset,
    mode: w.mode,
    quickAnswer: w.quickAnswer,
    dictResult: w.dictResult,
    deepThink: w.deepThink,
    corpusEntries: w.corpusEntries,
  }
}

export function fromSnapshot(s: TrackedWordSnapshot): TrackedWord {
  return {
    id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
    word: s.word,
    context: s.context,
    offset: s.offset,
    mode: s.mode,
    status: 'done',
    quickAnswer: s.quickAnswer,
    dictResult: s.dictResult,
    deepThink: s.deepThink,
    corpusEntries: s.corpusEntries,
    quickStatus: 'done',
    corpusStatus: 'done',
    dictStatus: 'done',
    deepStatus: s.deepThink ? 'done' : 'idle',
    startTime: Date.now(),
  }
}
