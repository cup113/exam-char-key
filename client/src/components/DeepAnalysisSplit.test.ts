import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import DeepAnalysisSplit from './DeepAnalysisSplit.vue'

describe('DeepAnalysisSplit', () => {
  it('renders context analysis when [解释] marker is present', () => {
    const wrapper = mount(DeepAnalysisSplit, {
      props: { deepThink: '[解释] 表示停顿\n[词义] 助词' }
    })
    expect(wrapper.text()).toContain('表示停顿')
    expect(wrapper.text()).toContain('语境分析')
  })

  it('renders fallback text when no markers are found', () => {
    const wrapper = mount(DeepAnalysisSplit, {
      props: { deepThink: '这是一段普通的分析文本' }
    })
    expect(wrapper.text()).toContain('这是一段普通的分析文本')
    expect(wrapper.text()).not.toContain('语境分析')
  })

  it('renders nothing when deepThink is empty', () => {
    const wrapper = mount(DeepAnalysisSplit, {
      props: { deepThink: '' }
    })
    expect(wrapper.text()).toBe('')
  })

  it('extracts text after [解释] marker', () => {
    const wrapper = mount(DeepAnalysisSplit, {
      props: { deepThink: '前言\n[解释] 核心解释\n[词义] 词义说明' }
    })
    expect(wrapper.text()).toContain('核心解释')
  })

  it('renders nothing when only [词义] is present (hasMarker=true, no [解释] match)', () => {
    const wrapper = mount(DeepAnalysisSplit, {
      props: { deepThink: '[词义] 助词' }
    })
    expect(wrapper.text()).toBe('')
  })
})
