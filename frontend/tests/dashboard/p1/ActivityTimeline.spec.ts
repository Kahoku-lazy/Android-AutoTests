/**
 * [P1] 建议测 — 最近活动时间线（条目渲染 / 类型样式 / 空态 / 分隔线）
 * 目录：tests/dashboard/p1/
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import ActivityTimeline from '@/modules/dashboard/components/ActivityTimeline.vue'
import { staggerReveal } from '@/shared/animations'
import type { ActivityItem } from '@/shared/types/dashboard'

vi.mock('@/shared/animations', () => ({
  staggerReveal: vi.fn(),
}))

const items: ActivityItem[] = [
  {
    type: 'success',
    action: '执行完成',
    time: '10:00',
    detail: '冒烟测试全部通过',
    tags: ['回归', 'P0'],
  },
  { type: 'error', action: '设备掉线', time: '09:30' },
]

function mountTimeline(props: { items?: ActivityItem[] } = {}) {
  return mount(ActivityTimeline, { props })
}

describe('[P1] ActivityTimeline', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('空列表：显示暂无活动记录', () => {
    const wrapper = mountTimeline({ items: [] })
    expect(wrapper.text()).toContain('暂无活动记录')
  })

  it('渲染条目：动作、时间、详情与标签', () => {
    const wrapper = mountTimeline({ items })
    const first = wrapper.findAll('.timeline-item')[0]

    expect(first.text()).toContain('执行完成')
    expect(first.text()).toContain('10:00')
    expect(first.text()).toContain('冒烟测试全部通过')
    expect(first.findAll('.timeline-item__tag')).toHaveLength(2)
    expect(first.text()).toContain('回归')
  })

  it('按 type：追加条目样式类', () => {
    const wrapper = mountTimeline({ items })

    const classes = wrapper.findAll('.timeline-item').map((i) => i.classes())
    expect(classes[0]).toContain('timeline-item--success')
    expect(classes[1]).toContain('timeline-item--error')
  })

  it('无 detail / tags 的条目：不渲染对应节点', () => {
    const wrapper = mountTimeline({ items })
    const second = wrapper.findAll('.timeline-item')[1]

    expect(second.find('.timeline-item__detail').exists()).toBe(false)
    expect(second.find('.timeline-item__tags').exists()).toBe(false)
  })

  it('分隔线：数量 = 条目数 - 1（最后一条无线）', () => {
    const wrapper = mountTimeline({ items })
    expect(wrapper.findAll('.timeline-item__line')).toHaveLength(items.length - 1)
  })

  it('条目数变化：重新触发 reveal 动画', async () => {
    const wrapper = mountTimeline({ items })
    await flushPromises()
    expect(staggerReveal).toHaveBeenCalledTimes(1)

    await wrapper.setProps({ items: [...items, { type: 'info', action: '新增', time: '11:00' }] })
    await flushPromises()

    expect(staggerReveal).toHaveBeenCalledTimes(2)
    expect(wrapper.findAll('.timeline-item')).toHaveLength(3)
  })
})
