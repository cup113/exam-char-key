import { describe, it, expect } from 'vitest'
import { getContextAround } from './context'

describe('getContextAround', () => {
  const text = '学而时习之，不亦说乎？有朋自远方来，不亦乐乎？人不知而不愠，不亦君子乎？'

  it('extracts window around offset in the middle', () => {
    const result = getContextAround(text, 5, 1, 3)
    expect(result).toContain('时习之')
    expect(result.startsWith('...')).toBe(true)
    expect(result.endsWith('...')).toBe(true)
  })

  it('adds leading ellipsis when not at start', () => {
    const result = getContextAround(text, 10, 1, 4)
    expect(result.startsWith('...')).toBe(true)
  })

  it('adds trailing ellipsis when not at end', () => {
    const result = getContextAround(text, 0, 1, 4)
    expect(result.endsWith('...')).toBe(true)
  })

  it('no ellipsis when context covers entire text', () => {
    const result = getContextAround(text, 10, 1, 100)
    expect(result.startsWith('...')).toBe(false)
    expect(result.endsWith('...')).toBe(false)
  })

  it('handles offset at start of text', () => {
    const result = getContextAround(text, 0, 2, 5)
    expect(result.startsWith('...')).toBe(false)
    expect(result).toContain('学而')
  })

  it('handles offset near end of text', () => {
    const result = getContextAround(text, text.length - 2, 2, 5)
    expect(result.endsWith('...')).toBe(false)
    expect(result).toContain('乎？')
  })

  it('uses custom window size', () => {
    const result = getContextAround(text, 5, 1, 2)
    expect(result).toBe('...习之，不亦...')
  })

  it('handles offset of 0 with default window', () => {
    const result = getContextAround(text, 0, 0)
    expect(result.endsWith('...')).toBe(true)
  })
})
