import { describe, it, expect } from 'vitest'
import { toSnapshot, fromSnapshot } from './document'
import type { TrackedWord, TrackedWordSnapshot } from '@/types'

function makeWord(overrides?: Partial<TrackedWord>): TrackedWord {
  return {
    id: 'test-id',
    word: '之',
    context: '之乎者也',
    offset: 0,
    mode: 'quick',
    status: 'done',
    quickAnswer: '代词',
    dictResult: '{}',
    deepThink: '',
    corpusEntries: [],
    quickStatus: 'done',
    corpusStatus: 'done',
    dictStatus: 'done',
    deepStatus: 'idle',
    startTime: 123456,
    ...overrides,
  }
}

describe('toSnapshot', () => {
  it('strips runtime fields', () => {
    const word = makeWord()
    const snapshot = toSnapshot(word)
    expect(snapshot).not.toHaveProperty('id')
    expect(snapshot).not.toHaveProperty('status')
    expect(snapshot).not.toHaveProperty('quickStatus')
    expect(snapshot).not.toHaveProperty('corpusStatus')
    expect(snapshot).not.toHaveProperty('dictStatus')
    expect(snapshot).not.toHaveProperty('deepStatus')
    expect(snapshot).not.toHaveProperty('startTime')
  })

  it('preserves all semantic fields', () => {
    const word = makeWord()
    const snapshot = toSnapshot(word)
    expect(snapshot.word).toBe('之')
    expect(snapshot.context).toBe('之乎者也')
    expect(snapshot.offset).toBe(0)
    expect(snapshot.mode).toBe('quick')
    expect(snapshot.quickAnswer).toBe('代词')
    expect(snapshot.dictResult).toBe('{}')
    expect(snapshot.deepThink).toBe('')
    expect(snapshot.corpusEntries).toEqual([])
  })
})

describe('fromSnapshot', () => {
  it('reconstructs a TrackedWord with generated id', () => {
    const snapshot: TrackedWordSnapshot = {
      word: '之',
      context: '之乎者也',
      offset: 0,
      mode: 'quick',
      quickAnswer: '代词',
      dictResult: '{}',
      deepThink: '',
      corpusEntries: [],
    }
    const word = fromSnapshot(snapshot)
    expect(word.id).toBeTruthy()
    expect(typeof word.id).toBe('string')
    expect(word.status).toBe('done')
    expect(word.quickStatus).toBe('done')
    expect(word.corpusStatus).toBe('done')
    expect(word.dictStatus).toBe('done')
    expect(word.deepStatus).toBe('idle')
    expect(word.startTime).toBeGreaterThan(0)
  })

  it('sets deepStatus to done when deepThink has content', () => {
    const snapshot: TrackedWordSnapshot = {
      word: '之',
      context: '',
      offset: 0,
      mode: 'deep',
      quickAnswer: '',
      dictResult: '',
      deepThink: 'deep analysis',
      corpusEntries: [],
    }
    const word = fromSnapshot(snapshot)
    expect(word.deepStatus).toBe('done')
  })

  it('preserves all snapshot fields', () => {
    const snapshot: TrackedWordSnapshot = {
      word: '也',
      context: '之乎者也',
      offset: 3,
      mode: 'deep',
      quickAnswer: '语气词',
      dictResult: '{"basic":[]}',
      deepThink: '表示判断',
      corpusEntries: [{ id: 1, type: 'classical', context: '...', word: '也', answer: '语气助词' }],
    }
    const word = fromSnapshot(snapshot)
    expect(word.word).toBe('也')
    expect(word.context).toBe('之乎者也')
    expect(word.offset).toBe(3)
    expect(word.mode).toBe('deep')
    expect(word.quickAnswer).toBe('语气词')
    expect(word.dictResult).toBe('{"basic":[]}')
    expect(word.deepThink).toBe('表示判断')
    expect(word.corpusEntries).toHaveLength(1)
    expect(word.corpusEntries[0]?.answer).toBe('语气助词')
  })
})
