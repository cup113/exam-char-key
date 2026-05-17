import { describe, it, expect, vi } from 'vitest'
import { readSSEStream } from './sse'

function createSSEResponse(chunks: string[]): Response {
  const encoder = new TextEncoder()
  const stream = new ReadableStream({
    async start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(chunk))
      }
      controller.close()
    },
  })
  return new Response(stream)
}

describe('readSSEStream', () => {
  it('parses data: lines and calls onChunk', async () => {
    const onChunk = vi.fn()
    const resp = createSSEResponse(['data: {"chunk":"hello"}\n\n', 'data: {"chunk":" world"}\n\n'])
    await readSSEStream(resp, onChunk)
    expect(onChunk).toHaveBeenCalledTimes(2)
    expect(onChunk).toHaveBeenNthCalledWith(1, 'hello')
    expect(onChunk).toHaveBeenNthCalledWith(2, ' world')
  })

  it('stops when [DONE] is received', async () => {
    const onChunk = vi.fn()
    const resp = createSSEResponse(['data: {"chunk":"hello"}\n\n', 'data: [DONE]\n\n', 'data: {"chunk":"ignored"}\n\n'])
    await readSSEStream(resp, onChunk)
    expect(onChunk).toHaveBeenCalledTimes(1)
  })

  it('skips malformed JSON lines silently', async () => {
    const onChunk = vi.fn()
    const resp = createSSEResponse(['data: not-json\n\n', 'data: {"chunk":"ok"}\n\n'])
    await readSSEStream(resp, onChunk)
    expect(onChunk).toHaveBeenCalledTimes(1)
    expect(onChunk).toHaveBeenCalledWith('ok')
  })

  it('handles chunked reads across buffer boundaries', async () => {
    const onChunk = vi.fn()
    const resp = createSSEResponse(['data: {"chunk":"he', 'llo"}\n\n'])
    await readSSEStream(resp, onChunk)
    expect(onChunk).toHaveBeenCalledWith('hello')
  })

  it('skips lines without data: prefix', async () => {
    const onChunk = vi.fn()
    const resp = createSSEResponse(['event: message\ndata: {"chunk":"only-data"}\n\n'])
    await readSSEStream(resp, onChunk)
    expect(onChunk).toHaveBeenCalledTimes(1)
    expect(onChunk).toHaveBeenCalledWith('only-data')
  })

  it('rethrows AbortError', async () => {
    const onChunk = vi.fn()
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(new TextEncoder().encode('data: {"chunk":"a"}\n\n'))
        const abortError = new DOMException('The operation was aborted', 'AbortError')
        controller.error(abortError)
      },
    })
    const resp = new Response(stream)
    await expect(readSSEStream(resp, onChunk)).rejects.toThrow('The operation was aborted')
  })
})
