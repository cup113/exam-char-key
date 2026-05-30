import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { nextTick } from 'vue'

const mockPreference: { value: boolean | null } = { value: null }

vi.mock('@vueuse/core', () => ({
  useLocalStorage: () => mockPreference,
}))

import { useThemeStore } from './theme'

function mockMatchMedia(matches: boolean) {
  vi.stubGlobal('matchMedia', vi.fn(() => ({
    matches,
    addEventListener: vi.fn(),
  })))
}

describe('useThemeStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    mockPreference.value = null
    document.documentElement.classList.remove('dark')
  })

  afterEach(() => {
    vi.clearAllMocks()
    vi.unstubAllGlobals()
  })

  it('initializes dark mode from system preference', () => {
    mockMatchMedia(true)
    const store = useThemeStore()
    expect(store.isDark).toBe(true)
  })

  it('initializes light mode from system preference', () => {
    mockMatchMedia(false)
    const store = useThemeStore()
    expect(store.isDark).toBe(false)
  })

  it('user preference takes precedence over system', () => {
    mockPreference.value = true
    mockMatchMedia(false)
    const store = useThemeStore()
    expect(store.isDark).toBe(true)
  })

  it('toggle switches dark mode', () => {
    mockMatchMedia(false)
    const store = useThemeStore()
    expect(store.isDark).toBe(false)
    store.toggle()
    expect(store.isDark).toBe(true)
    store.toggle()
    expect(store.isDark).toBe(false)
  })

  it('toggle persists user preference', () => {
    mockMatchMedia(false)
    const store = useThemeStore()
    store.toggle()
    expect(mockPreference.value).toBe(true)
    store.toggle()
    expect(mockPreference.value).toBe(false)
  })

  it('apply adds dark class when dark', () => {
    mockMatchMedia(true)
    useThemeStore()
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })

  it('apply removes dark class when light', () => {
    mockMatchMedia(false)
    useThemeStore()
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })

  it('apply updates class after toggle', async () => {
    mockMatchMedia(false)
    const store = useThemeStore()
    expect(document.documentElement.classList.contains('dark')).toBe(false)
    store.toggle()
    await nextTick()
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })
})
