import { describe, it, expect } from 'vitest'
import router from './index'

describe('router', () => {
  it('has all 5 routes', () => {
    expect(router.hasRoute('home')).toBe(true)
    expect(router.hasRoute('history')).toBe(true)
    expect(router.hasRoute('profile')).toBe(true)
    expect(router.hasRoute('admin')).toBe(true)
    expect(router.hasRoute('shared')).toBe(true)
  })

  it('resolves home route', () => {
    const resolved = router.resolve('/')
    expect(resolved.name).toBe('home')
  })

  it('resolves history route', () => {
    const resolved = router.resolve('/history')
    expect(resolved.name).toBe('history')
  })

  it('resolves profile route', () => {
    const resolved = router.resolve('/profile')
    expect(resolved.name).toBe('profile')
  })

  it('resolves admin route', () => {
    const resolved = router.resolve('/admin')
    expect(resolved.name).toBe('admin')
  })

  it('resolves shared route with uuid param', () => {
    const resolved = router.resolve('/shared/abc-123')
    expect(resolved.name).toBe('shared')
    expect(resolved.params.uuid).toBe('abc-123')
  })
})
