export function getContextAround(
  text: string,
  offset: number,
  wordLen: number,
  windowSize = 30,
): string {
  const start = Math.max(0, offset - windowSize)
  const end = Math.min(text.length, offset + wordLen + windowSize)
  let result = text.slice(start, end)
  if (start > 0) result = '...' + result
  if (end < text.length) result = result + '...'
  return result
}
