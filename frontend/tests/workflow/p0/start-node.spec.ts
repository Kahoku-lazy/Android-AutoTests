/**
 * [P0] 必测 — 页面流起点收敛为「启动 App / 起始页面」两种模式
 * 目录：tests/workflow/p0/
 *
 * 覆盖 `remove-page-flow-start-url-api` 的起点契约：
 *  1. 起点属性只写 start_kind / package_name，MUST NOT 写 start_url / start_api；
 *  2. 「启动 App」模式保留单一「启动」输出口；「起始页面」模式清空输出口并丢掉上一次的关联页面；
 *  3. 适配层把历史 url / api 取值降级为「启动 App」，且不再向节点数据暴露 URL / API 字段。
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

describe('页面流起点 — 模式与参数契约', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('新建起点默认是「启动 App」，属性只有 start_kind / package_name', () => {
    const { node } = seedStart()

    expect(node.properties.start_kind).toBe('app')
    expect(node.properties.package_name).toBe('com.example.app')
    expect(Object.keys(node.properties).sort()).toEqual(['package_name', 'start_kind'])
  })

  it('切换模式后仍不写入 start_url / start_api', () => {
    const { store, node } = seedStart()

    store.setStartKind(node.id, 'app')
    store.setStartKind(node.id, 'page')
    store.setStartKind(node.id, 'app')

    expect(Object.keys(node.properties).sort()).toEqual(['package_name', 'start_kind'])
    expect(node.properties.start_url).toBeUndefined()
    expect(node.properties.start_api).toBeUndefined()
  })

  it('「启动 App」模式保留单一「启动」输出口', () => {
    const { store, node } = seedStart()

    store.setStartKind(node.id, 'page')
    store.setStartKind(node.id, 'app')

    expect(node.outputs).toHaveLength(1)
    expect(node.outputs[0].name).toBe('启动')
    expect(node.outputs[0].type).toBe('navigation')
    expect(node.widgets_values[0]).toBe('启动 App')
  })

  it('「起始页面」模式清空输出口并丢掉上一次关联的页面', () => {
    const { store, node } = seedStart()

    store.setStartKind(node.id, 'page')
    store.linkPage(node.id, {
      id: 'p1',
      name: '主页',
      elements: [{ id: 'el_001', label: '登录', type: 'text' }],
    })
    expect(node.properties.linked_page_id).toBe('p1')
    expect(node.widgets_values[0]).toBe('主页')

    store.setStartKind(node.id, 'page')

    expect(node.outputs).toEqual([])
    expect(node.properties.linked_page_id).toBeUndefined()
    expect(node.properties.linked_page_name).toBeUndefined()
    expect(node.properties.linked_elements).toBeUndefined()
    expect(node.widgets_values[0]).toBe('起始页面')
  })
})

describe('页面流起点 — 适配层渲染数据', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('page 模式映射为 page，其余映射为 app', () => {
    const { store, node } = seedStart()

    store.setStartKind(node.id, 'page')
    expect(mappedData(node.id).startKind).toBe('page')

    store.setStartKind(node.id, 'app')
    expect(mappedData(node.id).startKind).toBe('app')
  })

  it('缺省 start_kind 的历史起点降级为 app', () => {
    const { node } = seedStart()
    delete node.properties.start_kind

    expect(mappedData(node.id).startKind).toBe('app')
  })

  it('历史 url / api 起点降级为 app，且不暴露 URL / API 字段', () => {
    const { node } = seedStart()

    for (const legacyKind of ['url', 'api']) {
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
