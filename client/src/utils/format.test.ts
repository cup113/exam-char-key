import { describe, it, expect } from 'vitest'
import { formatTime } from './format'

describe('formatTime', () => {
  it('converts ISO datetime to readable format', () => {
    expect(formatTime('2025-06-01T10:30:00')).toBe('2025-06-01 10:30')
  })

  it('handles datetime with timezone', () => {
    expect(formatTime('2025-06-01T10:30:00Z')).toBe('2025-06-01 10:30')
  })

  it('truncates seconds and beyond', () => {
    expect(formatTime('2025-01-15T08:45:30.123Z')).toBe('2025-01-15 08:45')
  })

  it('handles empty string', () => {
    expect(formatTime('')).toBe('')
  })
})
