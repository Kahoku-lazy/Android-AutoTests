/**
 * [P0] 必测 — 页面流起点只剩「启动 App」
 * 目录：tests/workflow/p0/
 *
 * 覆盖 `retire-inspector-and-element-locator` 的起点契约：
 *  1. 起点属性只写 start_kind / package_name，MUST NOT 写 start_url / start_api / linked_*；
 *  2. 起点保留单一「启动」输出口，不能承载元素输出口；
 *  3. 适配层把历史 page / url / api 取值一律降级为「启动 App」。
 */
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'

import { useWorkflowStore } from '@/modules/workflow/stores/workflowStore'
import { toVueFlowNodes } from '@/modules/workflow/composables/useVueFlowAdapter'

/** 新建一个起点节点；注册表限 1 个，每个用例都用全新 pinia，故不会撞上限 */
function seedStart() {
  const store = useWorkflowStore()
  const node = store.createNode('StartNode', 0, 0)
  if (!node) throw new Error('起点创建失败')
  return { store, node }
}

/** 取该起点在适配层里的节点渲染数据 */
function mappedData(nodeId: string) {
  const mapped = toVueFlowNodes(useWorkflowStore()).find(n => n.id === nodeId)
  if (!mapped) throw new Error('起点未出现在适配层输出中')
  return mapped.data
}

describe('页面流起点 — 只剩启动 App', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('新建起点是「启动 App」，属性只有 start_kind / package_name', () => {
    const { node } = seedStart()

    expect(node.properties.start_kind).toBe('app')
    expect(node.properties.package_name).toBe('com.example.app')
    expect(Object.keys(node.properties).sort()).toEqual(['package_name', 'start_kind'])
  })

  it('设置起点后仍只写两个属性，不写 start_url / start_api', () => {
    const { store, node } = seedStart()

    store.setStartKind(node.id, 'app')

    expect(Object.keys(node.properties).sort()).toEqual(['package_name', 'start_kind'])
    expect(node.properties.start_url).toBeUndefined()
    expect(node.properties.start_api).toBeUndefined()
  })

  it('起点保留单一「启动」输出口', () => {
    const { store, node } = seedStart()

    store.setStartKind(node.id, 'app')

    expect(node.outputs).toHaveLength(1)
    expect(node.outputs[0].name).toBe('启动')
    expect(node.outputs[0].type).toBe('navigation')
    expect(node.widgets_values[0]).toBe('启动 App')
  })

  it('起点不能创建元素输出口', () => {
    const { store, node } = seedStart()

    expect(store.canCreateOutput(node)).toBe(false)
  })

  it('历史残留的关联字段在写回时被清掉', () => {
    const { store, node } = seedStart()
    node.properties = {
      ...node.properties,
      linked_page_id: 'p1',
      linked_page_name: '主页',
      linked_elements: [{ id: 'el_001', label: '登录', type: 'text' }],
      linked_page_domain: 'android',
    }

    store.setStartKind(node.id, 'app')

    expect(node.properties.linked_page_id).toBeUndefined()
    expect(node.properties.linked_page_name).toBeUndefined()
    expect(node.properties.linked_elements).toBeUndefined()
    expect(node.properties.linked_page_domain).toBeUndefined()
  })
})

describe('页面流起点 — 适配层降级', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('缺省 start_kind 的历史起点降级为 app', () => {
    const { node } = seedStart()
    delete node.properties.start_kind

    expect(mappedData(node.id).startKind).toBe('app')
  })

  it('历史 page / url / api 起点降级为 app，且不暴露 URL / API 字段', () => {
    const { node } = seedStart()

    for (const legacyKind of ['page', 'url', 'api']) {
      node.properties = {
        start_kind: legacyKind,
        package_name: 'com.example.app',
        start_url: 'https://example.com',
        start_api: 'http://localhost/api/',
      }

      const data = mappedData(node.id)
      expect(data.startKind).toBe('app')
      expect(data.packageName).toBe('com.example.app')
      expect('startUrl' in data).toBe(false)
      expect('startApi' in data).toBe(false)
    }
  })
})
