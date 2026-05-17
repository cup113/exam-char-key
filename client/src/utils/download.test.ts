import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { downloadBlob } from './download'

describe('downloadBlob', () => {
  const mockCreateObjectURL = vi.fn(() => 'blob:mock-url')
  const mockRevokeObjectURL = vi.fn()
  let clickCount = 0

  let lastAnchor: { href: string; download: string; click: () => void }

  beforeEach(() => {
    clickCount = 0
    lastAnchor = { href: '', download: '', click: () => { clickCount++ } }
    vi.stubGlobal('URL', { createObjectURL: mockCreateObjectURL, revokeObjectURL: mockRevokeObjectURL })
    vi.stubGlobal('document', {
      createElement: vi.fn(() => lastAnchor),
    })
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('creates a blob URL and triggers download', () => {
    const blob = new Blob(['test'], { type: 'text/plain' })
    downloadBlob(blob, 'test.txt')
    expect(mockCreateObjectURL).toHaveBeenCalledWith(blob)
    expect(clickCount).toBe(1)
  })

  it('sets the filename on the anchor element', () => {
    const blob = new Blob(['test'])
    downloadBlob(blob, 'myfile.json')
    expect(lastAnchor.download).toBe('myfile.json')
    expect(lastAnchor.href).toBe('blob:mock-url')
  })

  it('revokes the blob URL after trigger', () => {
    const blob = new Blob(['test'])
    downloadBlob(blob, 'test.txt')
    expect(mockRevokeObjectURL).toHaveBeenCalledWith('blob:mock-url')
  })
})
