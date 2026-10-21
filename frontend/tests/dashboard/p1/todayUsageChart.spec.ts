/**
 * [P1] 建议测 — 今日用量折线点序列 + 跨零点自动刷新
 * 目录：tests/dashboard/p1/
 */
import { afterEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import { clockLabel, hourLabel, toHourlyPoints } from '@/modules/dashboard/helpers/hourlyPoints'
import { msUntilNextMidnight, useMidnightRefresh } from '@/modules/dashboard/composables/useMidnightRefresh'

describe('[P1] toHourlyPoints', () => {
  it('逐小时点落在整点（第 h 小时 → h+1 时刻），进行中窗口追加到当前时刻', () => {
    const values = [10, 20, null, null]

    const points = toHourlyPoints(values, 30, 3.5)

    expect(points).toEqual([
      [1, 10],
      [2, 20],
      [3.5, 30],
    ])
  })

  it('当前时刻不晚于最后一个点时：不重复追加', () => {
    const points = toHourlyPoints([10, 20, 30], 0, 3)

    expect(points).toEqual([
      [1, 10],
      [2, 20],
      [3, 30],
    ])
  })

  it('当前小时没有消耗时：不追加末端点，避免掉到 0 的假谷底', () => {
    expect(toHourlyPoints([10, 20, null], 0, 3.5)).toEqual([
      [1, 10],
      [2, 20],
    ])
  })

  it('没有进行中数据时：只有已走完的小时', () => {
    expect(toHourlyPoints([5, 6, null], undefined, undefined)).toEqual([
      [1, 5],
      [2, 6],
    ])
  })

  it('标签：刻度取整点，当前时刻带分钟', () => {
    expect(hourLabel(24)).toBe('24:00')
    expect(hourLabel(4)).toBe('04:00')
    expect(clockLabel(11.08)).toBe('11:05')
    expect(clockLabel(24)).toBe('24:00')
  })
})

function mountRollover(onRollover: () => void) {
  const Comp = defineComponent({
    setup() {
      useMidnightRefresh(onRollover)
      return () => h('div')
    },
  })
  return mount(Comp)
}

describe('[P1] useMidnightRefresh', () => {
  afterEach(() => {
    vi.useRealTimers()
  })

  it('距下一个零点：含 5 秒余量', () => {
    expect(msUntilNextMidnight(new Date(2026, 9, 21, 23, 59, 30))).toBe(30_000 + 5_000)
  })

  it('跨过本地零点：触发一次刷新', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 9, 21, 23, 59, 30))
    const onRollover = vi.fn()

    const wrapper = mountRollover(onRollover)
    expect(onRollover).not.toHaveBeenCalled()

    vi.advanceTimersByTime(36_000)

    expect(onRollover).toHaveBeenCalledTimes(1)
    wrapper.unmount()
  })

  it('卸载后：不再触发', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 9, 21, 23, 59, 30))
    const onRollover = vi.fn()

    const wrapper = mountRollover(onRollover)
    wrapper.unmount()
    vi.advanceTimersByTime(60_000)

    expect(onRollover).not.toHaveBeenCalled()
  })
})
