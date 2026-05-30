import { describe, it, expect } from 'vitest'
import { typeLabel, deepMeaning, aiAnswerForDict } from './wordAnalysis'

describe('typeLabel', () => {
  it('returns Chinese label for known types', () => {
    expect(typeLabel('textbook')).toBe('教材')
    expect(typeLabel('mock_exam')).toBe('模考')
    expect(typeLabel('user_query')).toBe('用户查询')
  })

  it('returns original string for unknown types', () => {
    expect(typeLabel('other')).toBe('other')
  })

  it('returns empty string for undefined', () => {
    expect(typeLabel(undefined)).toBe('')
  })
})

describe('deepMeaning', () => {
  it('extracts text after [词义] marker', () => {
    const text = '[词义] 代词，表示"的"\n[解释] 助词'
    expect(deepMeaning(text)).toBe('代词，表示"的"')
  })

  it('returns empty string when no [词义] marker', () => {
    const text = '[解释] 助词'
    expect(deepMeaning(text)).toBe('')
  })

  it('returns empty string for empty input', () => {
    expect(deepMeaning('')).toBe('')
  })

  it('captures full sentence including punctuation and spaces', () => {
    const text = '[词义] 代词，表示"的"'
    expect(deepMeaning(text)).toBe('代词，表示"的"')
  })

  it('returns first match when multiple [词义] lines exist', () => {
    const text = '[词义] 第一个\n[词义] 第二个'
    expect(deepMeaning(text)).toBe('第一个')
  })
})

describe('aiAnswerForDict', () => {
  it('returns both quick answer and deep meaning', () => {
    expect(aiAnswerForDict('代词', '[词义] 表示"的"')).toEqual(['代词', '表示"的"'])
  })

  it('returns only quick answer when no deep think', () => {
    expect(aiAnswerForDict('代词', '')).toEqual(['代词'])
  })

  it('returns empty string when no answers', () => {
    expect(aiAnswerForDict('', '')).toBe('')
  })
})
