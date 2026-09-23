/**
 * [P1] 建议测 — 最近活动时间线（十条槽 / 历史弹层 / 条目渲染）
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

const fetchRecentActivities = vi.fn()

vi.mock('@/modules/dashboard/api', () => ({
  fetchRecentActivities: (...args: unknown[]) => fetchRecentActivities(...args),
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

const ElDialogStub = {
  props: ['modelValue', 'title'],
  emits: ['update:modelValue'],
  template:
    '<div v-if="modelValue" class="stub-dialog" data-testid="history-dialog">' +
    '<header>{{ title }}</header><slot /><footer><slot name="footer" /></footer></div>',
}

function mountTimeline(props: { items?: ActivityItem[] } = {}) {
  return mount(ActivityTimeline, {
    props,
    global: {
      stubs: {
        'el-dialog': ElDialogStub,
        DoodleBtn: {
          template: '<button type="button" class="stub-doodle" @click="$emit(\'click\', $event)"><slot /></button>',
        },
      },
    },
  })
}

describe('[P1] ActivityTimeline', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    fetchRecentActivities.mockResolvedValue({
      data: { status: true, data: [] },
    })
  })

  it('空列表：显示暂无活动记录，且列表区保留十条槽类', () => {
    const wrapper = mountTimeline({ items: [] })
    expect(wrapper.text()).toContain('暂无活动记录')
    expect(wrapper.find('.timeline__list').exists()).toBe(true)
    expect(wrapper.find('.timeline__empty').exists()).toBe(true)
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

  it('标题行有「查看历史」按键', () => {
    const wrapper = mountTimeline({ items })
    expect(wrapper.text()).toContain('查看历史')
  })

  it('主屏最多渲染 10 条', () => {
    const many = Array.from({ length: 15 }, (_, i) => ({
      type: 'info',
      action: `a-${i}`,
      time: `10:${String(i).padStart(2, '0')}`,
    }))
    const wrapper = mountTimeline({ items: many })
    expect(wrapper.findAll('.timeline-item')).toHaveLength(10)
  })

  it('打开历史：请求 offset=10，空窗口显示没有更多历史记录', async () => {
    fetchRecentActivities.mockReset()
    fetchRecentActivities.mockResolvedValue({
      data: { status: true, data: [] },
    })
    const wrapper = mountTimeline({ items })
    await (wrapper.vm as { openHistory: () => Promise<void> }).openHistory()
    await flushPromises()

    expect(fetchRecentActivities).toHaveBeenCalledWith({ offset: 10, limit: 50 })
    expect(wrapper.find('[data-testid="history-dialog"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('没有更多历史记录')
    wrapper.unmount()
  })

  it('历史有数据且满页时可加载更多', async () => {
    const page = Array.from({ length: 50 }, (_, i) => ({
      type: 'run',
      action: `hist-${i}`,
      time: `09:${String(i % 60).padStart(2, '0')}`,
    }))
    const responses = [
      { data: { status: true, data: page } },
      {
        data: {
          status: true,
          data: [{ type: 'agent', action: '更多一条', time: '08:00' }],
        },
      },
    ]
    fetchRecentActivities.mockReset()
    fetchRecentActivities.mockImplementation(() => Promise.resolve(responses.shift()!))

    const wrapper = mountTimeline({ items })
    const vm = wrapper.vm as {
      openHistory: () => Promise<void>
      loadMoreHistory: () => void
      historyHasMore: boolean
    }
    await vm.openHistory()
    await flushPromises()

    expect(fetchRecentActivities).toHaveBeenCalledTimes(1)
    expect(fetchRecentActivities).toHaveBeenCalledWith({ offset: 10, limit: 50 })
    expect(wrapper.text()).toContain('hist-0')
    expect(vm.historyHasMore).toBe(true)
    expect(wrapper.text()).toContain('加载更多')

    vm.loadMoreHistory()
    await flushPromises()

    expect(fetchRecentActivities).toHaveBeenCalledTimes(2)
    expect(fetchRecentActivities).toHaveBeenLastCalledWith({ offset: 60, limit: 50 })
    expect(wrapper.text()).toContain('更多一条')
    wrapper.unmount()
  })
})
