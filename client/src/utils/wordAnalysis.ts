export function typeLabel(type: string | undefined): string {
  if (!type) return ''
  const map: Record<string, string> = {
    textbook: '教材',
    mock_exam: '模考',
    user_query: '用户查询',
  }
  return map[type] || type
}

export function deepMeaning(deepThink: string): string {
  if (!deepThink) return ''
  for (const line of deepThink.split('\n')) {
    const trimmed = line.trim()
    const match = trimmed.match(/^\[词义\]\s*(.*)$/)
    if (match) return match[1] || ''
  }
  return ''
}

export function aiAnswerForDict(
  quickAnswer: string,
  deepThink: string,
): string[] | string {
  const answers: string[] = []
  if (quickAnswer) answers.push(quickAnswer)
  const dm = deepMeaning(deepThink)
  if (dm) answers.push(dm)
  return answers.length > 0 ? answers : ''
}
