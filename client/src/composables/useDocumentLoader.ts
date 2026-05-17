import { ref } from 'vue'
import { useWordsStore } from '@/stores/words'
import type { DocumentRecord } from '@/types'
import type { ConfirmState, ConfirmButton } from '@/components/ConfirmDialog.vue'

export function useDocumentLoader() {
  const wordsStore = useWordsStore()
  const confirmState = ref<ConfirmState | null>(null)

  function confirm(title: string, message: string, buttons: ConfirmButton[]): Promise<string> {
    return new Promise(resolve => {
      confirmState.value = {
        show: true,
        title,
        message,
        buttons,
        resolve,
      }
    })
  }

  async function loadDocument(doc: DocumentRecord): Promise<boolean> {
    if (wordsStore.trackedWords.length > 0 && wordsStore.isDirty) {
      const action = await confirm(
        '未保存的更改',
        `当前会话有 ${wordsStore.trackedWords.length} 个查询结果未保存，加载文档将清除当前会话。`,
        [
          { label: '保存当前会话', value: 'save', variant: 'primary' },
          { label: '直接加载', value: 'discard' },
          { label: '取消', value: 'cancel' },
        ],
      )
      if (action === 'cancel') return false
      if (action === 'save') {
        try {
          await wordsStore.saveSnapshot(wordsStore.editableText.slice(0, 20), false)
        } catch {
          return false
        }
      }
    }
    wordsStore.importDocument(doc)
    return true
  }

  return { loadDocument, confirmState }
}
