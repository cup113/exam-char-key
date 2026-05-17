export async function readSSEStream(
  response: Response,
  onChunk: (chunk: string) => void,
): Promise<void> {
  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed.startsWith('data: ')) continue
        const payload = trimmed.slice(6)
        if (payload === '[DONE]') return
        try {
          const data = JSON.parse(payload)
          if (data.chunk) onChunk(data.chunk)
        } catch {
          // skip malformed JSON
        }
      }
    }
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') throw err
    console.error('SSE read error:', err)
    throw err
  }
}
