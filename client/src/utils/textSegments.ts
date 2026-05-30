import type { TrackedWord, TextSegment } from '@/types'

export function buildTextSegments(text: string, words: TrackedWord[]): TextSegment[] {
  const sorted = [...words]
    .filter(w => text.indexOf(w.word, w.offset) === w.offset)
    .sort((a, b) => a.offset - b.offset)

  const segments: TextSegment[] = []
  let cursor = 0
  for (const w of sorted) {
    if (w.offset < cursor) continue
    if (w.offset > cursor) {
      segments.push({ type: 'text', content: text.slice(cursor, w.offset) })
    }
    segments.push({ type: 'word', word: w })
    cursor = w.offset + w.word.length
  }
  if (cursor < text.length) {
    segments.push({ type: 'text', content: text.slice(cursor) })
  }
  return segments
}
