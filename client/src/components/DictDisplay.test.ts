import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import DictDisplay from './DictDisplay.vue'

describe('DictDisplay', () => {
  it('renders nothing when dictResult is null', () => {
    const wrapper = mount(DictDisplay, {
      props: { dictResult: null }
    })
    expect(wrapper.text()).toBe('')
  })

  it('renders nothing when dictResult is undefined', () => {
    const wrapper = mount(DictDisplay, {
      props: { dictResult: undefined }
    })
    expect(wrapper.text()).toBe('')
  })

  it('renders parsed basic explanation entries', () => {
    const wrapper = mount(DictDisplay, {
      props: {
        dictResult: JSON.stringify({
          basic_explanation: [
            { brief: '代词：这、此' },
            { brief: '连词：表示顺承' },
          ]
        }),
        queryWord: '之',
      }
    })
    expect(wrapper.text()).toContain('代词：这、此')
    expect(wrapper.text()).toContain('连词：表示顺承')
    expect(wrapper.text()).toContain('基本解释')
  })

  it('renders raw text when dictResult is not valid JSON', () => {
    const wrapper = mount(DictDisplay, {
      props: { dictResult: '汉典返回的纯文本结果' }
    })
    expect(wrapper.text()).toContain('汉典返回的纯文本结果')
  })

  it('renders detailed explanation with English annotations', () => {
    const wrapper = mount(DictDisplay, {
      props: {
        dictResult: JSON.stringify({
          detailed_explanation: [
            { brief: '用在动词前', english: 'used before a verb' }
          ]
        }),
      }
    })
    expect(wrapper.text()).toContain('用在动词前')
    expect(wrapper.text()).toContain('used before a verb')
    expect(wrapper.text()).toContain('详细解释')
  })

  it('renders examples for entries', () => {
    const wrapper = mount(DictDisplay, {
      props: {
        dictResult: JSON.stringify({
          basic_explanation: [
            { brief: '代词', examples: ['例一：...', '例二：...'] }
          ]
        }),
      }
    })
    expect(wrapper.text()).toContain('例一')
    expect(wrapper.text()).toContain('例二')
  })

  it('renders both sections when both are present', () => {
    const wrapper = mount(DictDisplay, {
      props: {
        dictResult: JSON.stringify({
          basic_explanation: [{ brief: '基本义' }],
          detailed_explanation: [{ brief: '详细义' }],
        }),
      }
    })
    expect(wrapper.text()).toContain('基本解释')
    expect(wrapper.text()).toContain('详细解释')
    expect(wrapper.text()).toContain('基本义')
    expect(wrapper.text()).toContain('详细义')
  })
})
