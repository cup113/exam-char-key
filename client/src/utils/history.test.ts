import { describe, it, expect, beforeEach } from 'vitest'
import { detectLegacyData, clearLegacyData } from './history'

beforeEach(() => {
  localStorage.clear()
})

describe('detectLegacyData', () => {
  it('returns null when no legacy data', () => {
    expect(detectLegacyData()).toBeNull()
  })

  it('returns parsed data when valid array exists', () => {
    const data = [{ id: '1', level: '1', front: '之', back: '代词', additions: [], createdAt: '2025-01-01' }]
    localStorage.setItem('EC_history', JSON.stringify(data))
    expect(detectLegacyData()).toEqual(data)
  })

  it('returns null when stored value is not an array', () => {
    localStorage.setItem('EC_history', JSON.stringify({ not: 'array' }))
    expect(detectLegacyData()).toBeNull()
  })

  it('returns null when stored array is empty', () => {
    localStorage.setItem('EC_history', JSON.stringify([]))
    expect(detectLegacyData()).toBeNull()
  })

  it('returns null on corrupt JSON', () => {
    localStorage.setItem('EC_history', 'not-json')
    expect(detectLegacyData()).toBeNull()
  })

  it('returns null when key does not exist', () => {
    expect(detectLegacyData()).toBeNull()
  })
})

describe('clearLegacyData', () => {
  it('removes the legacy storage key', () => {
    localStorage.setItem('EC_history', JSON.stringify([{ id: '1' }]))
    clearLegacyData()
    expect(localStorage.getItem('EC_history')).toBeNull()
  })
})
