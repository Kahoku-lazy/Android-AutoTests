/**
 * [P0] WorkbenchCrumbs — 返回芯片 + 波浪面包屑；末级不可点；reduced-motion 契约
 */
// @ts-nocheck — 本文件用 node:fs 读源码校验 CSS 契约，不纳入浏览器 DOM 类型
import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import WorkbenchCrumbs from '@/shared/components/WorkbenchCrumbs.vue'

async function mountCrumbs(props: Record<string, unknown> = {}) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: { template: '<div />' } },
      { path: '/cases', component: { template: '<div />' } },
      { path: '/cases/projects/1', component: { template: '<div />' } },
    ],
  })
  await router.push('/')
  return mount(WorkbenchCrumbs, {
    props: {
      backTo: '/cases',
      backLabel: '返回项目列表',
      items: [
        { label: '用例管理', to: '/cases' },
        { label: '项目工作台', to: '/cases/projects/1' },
        { label: '登录冒烟' },
      ],
      ...props,
    },
    global: { plugins: [router] },
  })
}

describe('[P0] WorkbenchCrumbs', () => {
  it('渲染返回芯片与面包屑；末级为当前页不可点', async () => {
    const wrapper = await mountCrumbs()
    expect(wrapper.find('.wb-crumbs__back').text()).toContain('返回项目列表')
    expect(wrapper.findAll('.wb-crumbs__link')).toHaveLength(2)
    expect(wrapper.find('.wb-crumbs__here').text()).toBe('登录冒烟')
    expect(wrapper.find('.wb-crumbs__here').attributes('aria-current')).toBe('page')
  })

  it('点击返回与祖先触发导航事件并 push', async () => {
    const wrapper = await mountCrumbs()
    const router = wrapper.vm.$.appContext.config.globalProperties.$router
    const push = vi.spyOn(router, 'push')
    await wrapper.find('.wb-crumbs__back').trigger('click')
    expect(wrapper.emitted('back')).toHaveLength(1)
    expect(push).toHaveBeenCalledWith('/cases')
    await wrapper.findAll('.wb-crumbs__link')[1].trigger('click')
    expect(wrapper.emitted('navigate')?.[0]).toEqual(['/cases/projects/1'])
  })

  it('源码含 prefers-reduced-motion 且关闭返回芯片 transform', () => {
    const src = readFileSync(
      resolve(dirname(fileURLToPath(import.meta.url)), '../../../src/shared/components/WorkbenchCrumbs.vue'),
      'utf8',
    )
    expect(src).toContain('prefers-reduced-motion: reduce')
    expect(src).toMatch(/\.wb-crumbs__back:(?:hover|active)[\s\S]*?transform:\s*none/)
  })
})
