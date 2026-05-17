import { apiClient, ApiError } from './apiClient'
import { readSSEStream } from '@/utils/sse'
import type { CorpusEntry } from '@/types'

interface ErrorBody {
  detail?: string
}

const FALLBACK_MESSAGES: Record<string, string> = {
  quick: '快速查询失败',
  corpus: '语料库查询失败',
  dict: '汉典查询失败',
  deep: '深度分析失败',
}

async function handleQueryError(resp: Response, label: string): Promise<never> {
  let detail = FALLBACK_MESSAGES[label]
  try {
    const body: ErrorBody = await resp.json()
    if (body.detail) detail = body.detail
  } catch {
    // use fallback
  }
  throw new ApiError(resp.status, detail || '请求失败')
}

export async function queryQuick(
  word: string,
  context: string,
  signal: AbortSignal,
  onChunk: (chunk: string) => void,
): Promise<void> {
  const resp = await apiClient.getRaw('/api/query/quick', {
    params: { word, context },
    signal,
  })
  if (!resp.ok) await handleQueryError(resp, 'quick')

  await readSSEStream(resp, onChunk)
}

export async function queryCorpus(
  word: string,
  signal: AbortSignal,
): Promise<CorpusEntry[]> {
  const resp = await apiClient.getRaw('/api/query/corpus', {
    params: { word },
    signal,
  })
  if (!resp.ok) await handleQueryError(resp, 'corpus')

  const data = await resp.json()
  return data.entries as CorpusEntry[]
}

export async function queryDictionary(
  word: string,
  signal: AbortSignal,
): Promise<string> {
  const resp = await apiClient.getRaw('/api/query/dictionary', {
    params: { word },
    signal,
  })
  if (!resp.ok) await handleQueryError(resp, 'dict')

  const data = await resp.json()
  return data.result as string
}

export async function queryDeep(
  word: string,
  context: string,
  signal: AbortSignal,
  onChunk: (chunk: string) => void,
): Promise<void> {
  const resp = await apiClient.getRaw('/api/query/deep', {
    params: { word, context },
    signal,
  })
  if (!resp.ok) await handleQueryError(resp, 'deep')

  await readSSEStream(resp, onChunk)
}
