import { ref, type Ref } from 'vue'

export function useRangeSelection<T extends { id: number }>(items: Ref<T[]>) {
  const toggledIds = ref<Set<number>>(new Set())
  const autoCheckedIds = ref<Set<number>>(new Set())
  const checkedIds = ref<Set<number>>(new Set())

  function recalculateChecked() {
    const filtered = items.value
    const manual = [...toggledIds.value].filter(id => filtered.some(r => r.id === id))

    if (manual.length >= 2) {
      const indices = manual.map(id => filtered.findIndex(r => r.id === id)).sort((a, b) => a - b)
      const minIdx = indices[0]!
      const maxIdx = indices[indices.length - 1]!

      const newChecked = new Set(manual)
      const newAuto = new Set<number>()
      for (let i = minIdx + 1; i < maxIdx; i++) {
        const r = filtered[i]
        if (r && !newChecked.has(r.id)) {
          newChecked.add(r.id)
          newAuto.add(r.id)
        }
      }

      checkedIds.value = newChecked
      autoCheckedIds.value = newAuto
    } else {
      checkedIds.value = new Set(manual)
      autoCheckedIds.value = new Set()
    }
  }

  function handleCheck(id: number) {
    if (checkedIds.value.has(id)) {
      if (autoCheckedIds.value.has(id)) {
        const newChecked = new Set(toggledIds.value)
        checkedIds.value = newChecked
        autoCheckedIds.value = new Set()
      } else {
        const newToggled = new Set(toggledIds.value)
        newToggled.delete(id)
        toggledIds.value = newToggled
        recalculateChecked()
      }
    } else {
      const newToggled = new Set(toggledIds.value)
      newToggled.add(id)
      toggledIds.value = newToggled
      recalculateChecked()
    }
  }

  function removeId(id: number) {
    const newToggled = new Set(toggledIds.value)
    newToggled.delete(id)
    toggledIds.value = newToggled
    const newAuto = new Set(autoCheckedIds.value)
    newAuto.delete(id)
    autoCheckedIds.value = newAuto
    const newChecked = new Set(checkedIds.value)
    newChecked.delete(id)
    checkedIds.value = newChecked
  }

  function clearAll() {
    toggledIds.value = new Set()
    autoCheckedIds.value = new Set()
    checkedIds.value = new Set()
  }

  return { checkedIds, handleCheck, clearAll, removeId }
}
