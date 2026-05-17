import { describe, it, expect } from 'vitest'
import { ref } from 'vue'
import { useRangeSelection } from './useRangeSelection'

interface TestItem { id: number; name: string }

const items = ref<TestItem[]>([
  { id: 1, name: 'a' },
  { id: 2, name: 'b' },
  { id: 3, name: 'c' },
  { id: 4, name: 'd' },
  { id: 5, name: 'e' },
])

describe('useRangeSelection', () => {
  it('starts with empty selection', () => {
    const { checkedIds } = useRangeSelection(items)
    expect(checkedIds.value.size).toBe(0)
  })

  it('checks a single id', () => {
    const { checkedIds, handleCheck } = useRangeSelection(items)
    handleCheck(2)
    expect(checkedIds.value.has(2)).toBe(true)
    expect(checkedIds.value.size).toBe(1)
  })

  it('fills range between two checked items', () => {
    const { checkedIds, handleCheck } = useRangeSelection(items)
    handleCheck(1)
    handleCheck(5)
    expect(checkedIds.value.size).toBe(5)
    for (let i = 1; i <= 5; i++) {
      expect(checkedIds.value.has(i)).toBe(true)
    }
  })

  it('fills range in reverse order', () => {
    const { checkedIds, handleCheck } = useRangeSelection(items)
    handleCheck(5)
    handleCheck(1)
    expect(checkedIds.value.size).toBe(5)
  })

  it('unchecks a manually checked item', () => {
    const { checkedIds, handleCheck } = useRangeSelection(items)
    handleCheck(2)
    expect(checkedIds.value.has(2)).toBe(true)
    handleCheck(2)
    expect(checkedIds.value.has(2)).toBe(false)
    expect(checkedIds.value.size).toBe(0)
  })

  it('removes an auto-checked item on manual uncheck', () => {
    const { checkedIds, handleCheck } = useRangeSelection(items)
    handleCheck(1)
    handleCheck(5)
    expect(checkedIds.value.size).toBe(5)
    // id 3 is auto-checked - unchecking it should remove all auto items
    handleCheck(3)
    expect(checkedIds.value.size).toBe(2)
    expect(checkedIds.value.has(1)).toBe(true)
    expect(checkedIds.value.has(5)).toBe(true)
  })

  it('clears all', () => {
    const { checkedIds, handleCheck, clearAll } = useRangeSelection(items)
    handleCheck(1)
    handleCheck(5)
    expect(checkedIds.value.size).toBe(5)
    clearAll()
    expect(checkedIds.value.size).toBe(0)
  })

  it('removeId removes from all sets', () => {
    const { checkedIds, handleCheck, removeId } = useRangeSelection(items)
    handleCheck(2)
    handleCheck(4)
    expect(checkedIds.value.size).toBe(3)
    removeId(2)
    expect(checkedIds.value.has(2)).toBe(false)
  })
})
