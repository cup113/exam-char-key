import { describe, it, expect } from 'vitest'
import { buildTextSegments } from './textSegments'
import type { TrackedWord } from '@/types'

function word(overrides: Partial<TrackedWord> & { word: string; offset: number }): TrackedWord {
  return {
    id: 'test-id',
    context: '',
    mode: 'quick',
    status: 'done',
    quickAnswer: '',
    dictResult: '',
    deepThink: '',
    corpusEntries: [],
    quickStatus: 'done',
    corpusStatus: 'done',
    dictStatus: 'done',
    deepStatus: 'idle',
    startTime: 0,
    ...overrides,
  }
}

describe('buildTextSegments', () => {
  const text = '学而时习之，不亦说乎？'

  it('returns single text segment when no words', () => {
    const result = buildTextSegments(text, [])
    expect(result).toEqual([{ type: 'text', content: text }])
  })

  it('builds segments with one tracked word', () => {
    const w = word({ word: '习', offset: 3 })
    const result = buildTextSegments(text, [w])
    expect(result).toHaveLength(3)
    expect(result[0]).toEqual({ type: 'text', content: '学而时' })
    expect(result[1]).toEqual({ type: 'word', word: w })
    expect(result[2]).toEqual({ type: 'text', content: '之，不亦说乎？' })
  })

  it('handles multiple words in order', () => {
    const w1 = word({ word: '学而', offset: 0 })
    const w2 = word({ word: '说', offset: 8 })
    const result = buildTextSegments(text, [w2, w1])
    expect(result).toHaveLength(4)
    expect(result[0]).toEqual({ type: 'word', word: w1 })
    expect(result[1]).toEqual({ type: 'text', content: '时习之，不亦' })
    expect(result[2]).toEqual({ type: 'word', word: w2 })
    expect(result[3]).toEqual({ type: 'text', content: '乎？' })
  })

  it('skips words with mismatched offset', () => {
    const w = word({ word: '习', offset: 10 })
    const result = buildTextSegments(text, [w])
    expect(result).toEqual([{ type: 'text', content: text }])
  })

  it('skips overlapping words', () => {
    const w1 = word({ word: '学而时习', offset: 0 })
    const w2 = word({ word: '时习', offset: 2 })
    const result = buildTextSegments(text, [w1, w2])
    expect(result).toHaveLength(2)
    expect(result[0]).toEqual({ type: 'word', word: w1 })
    expect(result[1]).toEqual({ type: 'text', content: '之，不亦说乎？' })
  })

  it('handles word at end of text', () => {
    const w = word({ word: '乎？', offset: 9 })
    const result = buildTextSegments(text, [w])
    expect(result).toHaveLength(2)
    expect(result[0]).toEqual({ type: 'text', content: '学而时习之，不亦说' })
    expect(result[1]).toEqual({ type: 'word', word: w })
  })

  it('handles word at start of text', () => {
    const w = word({ word: '学而', offset: 0 })
    const result = buildTextSegments(text, [w])
    expect(result).toHaveLength(2)
    expect(result[0]).toEqual({ type: 'word', word: w })
    expect(result[1]).toEqual({ type: 'text', content: '时习之，不亦说乎？' })
  })

  it('handles all text being covered by words', () => {
    const w1 = word({ word: '学而时习之', offset: 0 })
    const w2 = word({ word: '，不亦说乎？', offset: 5 })
    const result = buildTextSegments(text, [w1, w2])
    expect(result).toHaveLength(2)
    expect(result[0]).toEqual({ type: 'word', word: w1 })
    expect(result[1]).toEqual({ type: 'word', word: w2 })
  })
})
