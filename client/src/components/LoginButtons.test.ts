import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import LoginButtons from './LoginButtons.vue'

describe('LoginButtons', () => {
  it('renders two login links', () => {
    const wrapper = mount(LoginButtons)
    const links = wrapper.findAll('a')
    expect(links).toHaveLength(2)
    expect(links[0].text()).toBe('GitHub 登录')
    expect(links[1].text()).toBe('Gitee 登录')
  })

  it('links point to correct OAuth URLs', () => {
    const wrapper = mount(LoginButtons)
    const links = wrapper.findAll('a')
    expect(links[0].attributes('href')).toBe('/api/auth/github/login')
    expect(links[1].attributes('href')).toBe('/api/auth/gitee/login')
  })

  it('uses sm classes when size is sm', () => {
    const wrapper = mount(LoginButtons, { props: { size: 'sm' } })
    const links = wrapper.findAll('a')
    for (const link of links) {
      expect(link.classes()).toContain('px-3')
      expect(link.classes()).toContain('py-1.5')
      expect(link.classes()).toContain('text-xs')
    }
  })

  it('uses md classes by default', () => {
    const wrapper = mount(LoginButtons)
    const links = wrapper.findAll('a')
    for (const link of links) {
      expect(link.classes()).toContain('px-4')
      expect(link.classes()).toContain('py-2')
      expect(link.classes()).toContain('text-sm')
    }
  })
})
