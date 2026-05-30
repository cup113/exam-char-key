import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'

const { checkedIds } = vi.hoisted(() => {
  const _checkedIds: { __v_isRef: true; value: Set<number> } = {
    __v_isRef: true,
    value: new Set<number>(),
  }
  return {
    checkedIds: _checkedIds,
    useRangeSelectionMock: () => ({
      checkedIds: _checkedIds,
      handleCheck: vi.fn((id: number) => _checkedIds.value.add(id)),
      clearAll: vi.fn(() => _checkedIds.value.clear()),
      removeId: vi.fn(),
    }),
  }
})

vi.mock('@/stores/auth', () => ({
  useAuthStore: vi.fn(),
}))

vi.mock('@/composables/useRangeSelection', () => ({
  useRangeSelection: vi.fn(() => ({
    checkedIds,
    handleCheck: vi.fn((id: number) => checkedIds.value.add(id)),
    clearAll: vi.fn(() => checkedIds.value.clear()),
    removeId: vi.fn(),
  })),
}))

vi.mock('@/services/historyService', () => ({
  listHistory: vi.fn(),
  deleteHistory: vi.fn(),
  batchDeleteHistory: vi.fn(),
}))

vi.mock('@/services/exportService', () => ({
  exportRecords: vi.fn(),
}))

vi.mock('@/services/migrateService', () => ({
  migrateLegacyData: vi.fn(),
}))

import { useAuthStore } from '@/stores/auth'
import * as historyService from '@/services/historyService'
import { exportRecords } from '@/services/exportService'
import { migrateLegacyData } from '@/services/migrateService'
import HistoryView from './HistoryView.vue'

function flushMicrotasks() {
  return new Promise(resolve => setTimeout(resolve, 0))
}

function mockRecords() {
  return [
    { id: 1, word: '之', context: '学而时习之', mode: 'quick', quick_answer: '代词', dict_result: '', deep_think: '', created_at: '2025-06-01T10:30:00' },
    { id: 2, word: '乎', context: '不亦乐乎', mode: 'deep', quick_answer: '语气词', dict_result: '文言助词', deep_think: '表示疑问', created_at: '2025-06-02T14:00:00' },
  ]
}

describe('HistoryView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    checkedIds.value = new Set<number>()
    vi.stubGlobal('confirm', vi.fn(() => true))
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.clearAllMocks()
  })

  it('shows loading state initially', () => {
    vi.mocked(historyService.listHistory).mockReturnValue(new Promise(() => {}))
    vi.mocked(useAuthStore).mockReturnValue({
      user: { logged_in: true },
      fetchUser: vi.fn().mockResolvedValue(undefined),
    } as any)

    const wrapper = mount(HistoryView)
    expect(wrapper.text()).toContain('加载中')
  })

  it('shows login prompt when not logged in', async () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { logged_in: false },
      fetchUser: vi.fn().mockResolvedValue(undefined),
    } as any)

    const wrapper = mount(HistoryView)
    await flushMicrotasks()
    expect(wrapper.text()).toContain('请先登录')
  })

  it('shows empty state when no records', async () => {
    vi.mocked(historyService.listHistory).mockResolvedValue({ records: [] })
    vi.mocked(useAuthStore).mockReturnValue({
      user: { logged_in: true },
      fetchUser: vi.fn().mockResolvedValue(undefined),
    } as any)

    const wrapper = mount(HistoryView)
    await flushMicrotasks()
    expect(wrapper.text()).toContain('暂无保存记录')
  })

  it('renders records when loaded', async () => {
    vi.mocked(historyService.listHistory).mockResolvedValue({ records: mockRecords() })
    vi.mocked(useAuthStore).mockReturnValue({
      user: { logged_in: true },
      fetchUser: vi.fn().mockResolvedValue(undefined),
    } as any)

    const wrapper = mount(HistoryView)
    await flushMicrotasks()
    expect(wrapper.text()).toContain('之')
    expect(wrapper.text()).toContain('乎')
    expect(wrapper.text()).toContain('2 条记录')
  })

  it('filters records by search query', async () => {
    vi.mocked(historyService.listHistory).mockResolvedValue({ records: mockRecords() })
    vi.mocked(useAuthStore).mockReturnValue({
      user: { logged_in: true },
      fetchUser: vi.fn().mockResolvedValue(undefined),
    } as any)

    const wrapper = mount(HistoryView)
    await flushMicrotasks()

    const input = wrapper.find('input[type="text"]')
    await input.setValue('乎')
    await flushMicrotasks()

    expect(wrapper.text()).toContain('乎')
    expect(wrapper.text()).not.toContain('之')
  })

  it('expands and collapses a record', async () => {
    vi.mocked(historyService.listHistory).mockResolvedValue({ records: mockRecords() })
    vi.mocked(useAuthStore).mockReturnValue({
      user: { logged_in: true },
      fetchUser: vi.fn().mockResolvedValue(undefined),
    } as any)

    const wrapper = mount(HistoryView)
    await flushMicrotasks()

    const expandBtns = wrapper.findAll('button').filter(b => /展开/.test(b.text()))
    expect(expandBtns.length).toBeGreaterThan(0)
    await expandBtns[0]!.trigger('click')
    await flushMicrotasks()

    expect(wrapper.text()).toContain('收起')
    expect(wrapper.text()).toContain('⚡ 快速回答')
  })

  it('deletes a single record with confirmation', async () => {
    vi.mocked(historyService.listHistory).mockResolvedValue({ records: mockRecords() })
    vi.mocked(historyService.deleteHistory).mockResolvedValue(undefined)
    vi.mocked(useAuthStore).mockReturnValue({
      user: { logged_in: true },
      fetchUser: vi.fn().mockResolvedValue(undefined),
    } as any)

    const wrapper = mount(HistoryView)
    await flushMicrotasks()

    const deleteBtns = wrapper.findAll('button[title="删除"]')
    expect(deleteBtns.length).toBeGreaterThan(0)
    await deleteBtns[0]!.trigger('click')
    await flushMicrotasks()

    expect(historyService.deleteHistory).toHaveBeenCalledWith(1)
    expect(wrapper.text()).not.toContain('之')
  })

  it('exports records', async () => {
    vi.mocked(historyService.listHistory).mockResolvedValue({ records: mockRecords() })
    vi.mocked(exportRecords).mockResolvedValue(undefined)
    vi.mocked(useAuthStore).mockReturnValue({
      user: { logged_in: true },
      fetchUser: vi.fn().mockResolvedValue(undefined),
    } as any)

    const wrapper = mount(HistoryView)
    await flushMicrotasks()

    const jsonBtns = wrapper.findAll('button').filter(b => b.text().trim() === 'JSON')
    expect(jsonBtns.length).toBeGreaterThan(0)
    await jsonBtns[0]!.trigger('click')
    await flushMicrotasks()

    expect(exportRecords).toHaveBeenCalledWith('json', undefined)
  })

  it('shows legacy migration banner when legacy data found', async () => {
    localStorage.setItem('EC_history', JSON.stringify([{ id: '1', level: '1', front: '之', back: '代词', additions: [], createdAt: '2025-01-01' }]))
    vi.mocked(historyService.listHistory).mockResolvedValue({ records: [] })
    vi.mocked(useAuthStore).mockReturnValue({
      user: { logged_in: true },
      fetchUser: vi.fn().mockResolvedValue(undefined),
    } as any)

    const wrapper = mount(HistoryView)
    await flushMicrotasks()
    expect(wrapper.text()).toContain('检测到旧版数据')
  })

  it('migrates legacy data successfully', async () => {
    localStorage.setItem('EC_history', JSON.stringify([{ id: '1', level: '1', front: '之', back: '代词', additions: [], createdAt: '2025-01-01' }]))
    vi.mocked(historyService.listHistory).mockResolvedValue({ records: [] })
    vi.mocked(migrateLegacyData).mockResolvedValue(undefined)
    vi.mocked(useAuthStore).mockReturnValue({
      user: { logged_in: true },
      fetchUser: vi.fn().mockResolvedValue(undefined),
    } as any)

    const wrapper = mount(HistoryView)
    await flushMicrotasks()

    const migrateBtns = wrapper.findAll('button').filter(b => /迁移/.test(b.text()))
    expect(migrateBtns.length).toBeGreaterThan(0)
    await migrateBtns[0]!.trigger('click')
    await flushMicrotasks()

    expect(migrateLegacyData).toHaveBeenCalled()
    expect(wrapper.text()).toContain('迁移完成')
  })

  it('shows export error', async () => {
    vi.mocked(historyService.listHistory).mockResolvedValue({ records: mockRecords() })
    vi.mocked(exportRecords).mockRejectedValue(new Error('导出失败'))
    vi.mocked(useAuthStore).mockReturnValue({
      user: { logged_in: true },
      fetchUser: vi.fn().mockResolvedValue(undefined),
    } as any)

    const wrapper = mount(HistoryView)
    await flushMicrotasks()

    const jsonBtns = wrapper.findAll('button').filter(b => b.text().trim() === 'JSON')
    expect(jsonBtns.length).toBeGreaterThan(0)
    await jsonBtns[0]!.trigger('click')
    await flushMicrotasks()

    expect(wrapper.text()).toContain('导出失败')
  })
})
