/**
 * [P0] 必测 — 任务详情报告自动刷新调度
 * 目录：tests/task-list/p0/
 *
 * 覆盖 spec「运行中任务详情页按 3 秒轮询」「刷新静默且失败退避」里的调度侧行为：
 * 到点触发、不叠加、退避序列、可见性暂停与回补、终态停止、卸载清理、间隔 <= 0 关闭。
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { useReportPoll } from '@/modules/task-list/composables/useReportPoll'
import { mountComposable } from '../../helpers/mountComposable'
import type { ReportPollOptions } from '@/modules/task-list/composables/useReportPoll'

/** 手动控制何时 resolve 的 promise */
function deferred() {
  let resolve!: (value: boolean) => void
  const promise = new Promise<boolean>((r) => {
    resolve = r
  })
  return { promise, resolve }
}

/** 把 document.hidden 改成指定值（jsdom 下是只读 getter） */
function setHidden(value: boolean) {
  Object.defineProperty(document, 'hidden', { configurable: true, get: () => value })
}

/** 挂一个默认成功的轮询；active 由调用方控制 */
async function mountPoll(
  options: {
    refresh?: () => Promise<boolean>
    isActive?: () => boolean
    pollOptions?: ReportPollOptions
  } = {},
  mountOptions: { keepAlive?: boolean } = {},
) {
  const refresh = vi.fn(options.refresh ?? (() => Promise.resolve(true)))
  const isActive = vi.fn(options.isActive ?? (() => true))
  const mounted = await mountComposable(
    () => useReportPoll(refresh, isActive, options.pollOptions),
    mountOptions,
  )
  return { ...mounted, refresh, isActive }
}

describe('[P0] useReportPoll', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    setHidden(false)
  })

  afterEach(() => {
    vi.useRealTimers()
    setHidden(false)
    vi.restoreAllMocks()
  })

  it('开始后每 3 秒触发一次', async () => {
    const { result, refresh } = await mountPoll()

    result.start()
    expect(result.polling.value).toBe(true)

    await vi.advanceTimersByTimeAsync(3000)
    await flushPromises()
    expect(refresh).toHaveBeenCalledTimes(1)

    await vi.advanceTimersByTimeAsync(3000)
    await flushPromises()
    expect(refresh).toHaveBeenCalledTimes(2)
    expect(result.lastUpdatedAt.value).toBeInstanceOf(Date)
  })

  it('上一轮没回来不叠加第二次', async () => {
    const pending = deferred()
    const { result, refresh } = await mountPoll({ refresh: () => pending.promise })

    result.start()
    await vi.advanceTimersByTimeAsync(3000)
    expect(refresh).toHaveBeenCalledTimes(1)

    // 请求还在途，再过三个周期也不发新请求
    await vi.advanceTimersByTimeAsync(9000)
    expect(refresh).toHaveBeenCalledTimes(1)

    pending.resolve(true)
    await flushPromises()
    await vi.advanceTimersByTimeAsync(3000)
    expect(refresh).toHaveBeenCalledTimes(2)
  })

  it('连续失败按 3/6/12/30 秒退避', async () => {
    const { result, refresh } = await mountPoll({ refresh: () => Promise.resolve(false) })

    result.start()
    await vi.advanceTimersByTimeAsync(3000)
    expect(refresh).toHaveBeenCalledTimes(1)

    // 第 1 次失败后仍按 3 秒重试
    await vi.advanceTimersByTimeAsync(2999)
    expect(refresh).toHaveBeenCalledTimes(1)
    await vi.advanceTimersByTimeAsync(1)
    expect(refresh).toHaveBeenCalledTimes(2)

    // 第 2 次失败后 6 秒
    await vi.advanceTimersByTimeAsync(5999)
    expect(refresh).toHaveBeenCalledTimes(2)
    await vi.advanceTimersByTimeAsync(1)
    expect(refresh).toHaveBeenCalledTimes(3)

    // 第 3 次失败后 12 秒
    await vi.advanceTimersByTimeAsync(11999)
    expect(refresh).toHaveBeenCalledTimes(3)
    await vi.advanceTimersByTimeAsync(1)
    expect(refresh).toHaveBeenCalledTimes(4)

    // 第 4 次失败后 30 秒封顶
    await vi.advanceTimersByTimeAsync(30000)
    expect(refresh).toHaveBeenCalledTimes(5)
  })

  it('连续失败 6 次后停止并置 failed', async () => {
    const { result, refresh } = await mountPoll({ refresh: () => Promise.resolve(false) })

    result.start()
    // 3 + 6 + 12 + 30 + 30 + 30 秒后达到上限
    await vi.advanceTimersByTimeAsync(3000 + 6000 + 12000 + 30000 + 30000 + 30000)
    await flushPromises()

    expect(refresh).toHaveBeenCalledTimes(6)
    expect(result.failed.value).toBe(true)
    expect(result.polling.value).toBe(false)

    await vi.advanceTimersByTimeAsync(60000)
    expect(refresh).toHaveBeenCalledTimes(6)
  })

  it('页面隐藏期间不请求，回到可见立即补一次', async () => {
    const { result, refresh } = await mountPoll()

    setHidden(true)
    result.start()
    await vi.advanceTimersByTimeAsync(9000)
    expect(refresh).not.toHaveBeenCalled()

    setHidden(false)
    document.dispatchEvent(new Event('visibilitychange'))
    await flushPromises()
    expect(refresh).toHaveBeenCalledTimes(1)

    await vi.advanceTimersByTimeAsync(3000)
    expect(refresh).toHaveBeenCalledTimes(2)
  })

  it('任务进终态后不再调度', async () => {
    let active = true
    const { result, refresh } = await mountPoll({ isActive: () => active })

    result.start()
    await vi.advanceTimersByTimeAsync(3000)
    expect(refresh).toHaveBeenCalledTimes(1)

    active = false
    await vi.advanceTimersByTimeAsync(3000)
    expect(refresh).toHaveBeenCalledTimes(1)
    expect(result.polling.value).toBe(false)
  })

  it('卸载后无残留定时器', async () => {
    const { result, refresh, wrapper } = await mountPoll()

    result.start()
    wrapper.unmount()
    await vi.advanceTimersByTimeAsync(30000)

    expect(refresh).not.toHaveBeenCalled()
    expect(result.polling.value).toBe(false)
  })

  it('间隔为 0 视为关闭自动刷新', async () => {
    const { result, refresh } = await mountPoll({ pollOptions: { intervalMs: 0 } })

    result.start()
    await vi.advanceTimersByTimeAsync(30000)

    expect(refresh).not.toHaveBeenCalled()
    expect(result.polling.value).toBe(false)
  })

  it('restart 立即重试并恢复轮询', async () => {
    let ok = false
    const { result, refresh } = await mountPoll({ refresh: () => Promise.resolve(ok) })

    result.start()
    await vi.advanceTimersByTimeAsync(3000 + 6000 + 12000 + 30000 + 30000 + 30000)
    await flushPromises()
    expect(result.failed.value).toBe(true)

    ok = true
    result.restart()
    await vi.advanceTimersByTimeAsync(0)
    await flushPromises()

    expect(result.failed.value).toBe(false)
    expect(result.polling.value).toBe(true)
    expect(refresh).toHaveBeenCalledTimes(7)
  })

  it('离开页面（keep-alive 失活）后不再请求，回到页面立即补一次', async () => {
    const { result, refresh, deactivate, activate } = await mountPoll({}, { keepAlive: true })

    result.start()
    await vi.advanceTimersByTimeAsync(3000)
    await flushPromises()
    expect(refresh).toHaveBeenCalledTimes(1)

    // 页面被 keep-alive 缓存：不卸载，只失活
    await deactivate?.()
    await vi.advanceTimersByTimeAsync(60000)
    await flushPromises()
    expect(refresh).toHaveBeenCalledTimes(1)
    expect(result.polling.value).toBe(false)

    // 回到页面：立即补一次，不等 3 秒周期
    await activate?.()
    await vi.advanceTimersByTimeAsync(0)
    await flushPromises()
    expect(refresh).toHaveBeenCalledTimes(2)
    expect(result.polling.value).toBe(true)
  })

  it('失活期间不恢复调用方已停止的轮询', async () => {
    const { result, refresh, deactivate, activate } = await mountPoll({}, { keepAlive: true })

    result.start()
    await vi.advanceTimersByTimeAsync(3000)
    await flushPromises()
    expect(refresh).toHaveBeenCalledTimes(1)

    result.stop()
    await deactivate?.()
    await activate?.()
    await vi.advanceTimersByTimeAsync(30000)
    await flushPromises()

    expect(refresh).toHaveBeenCalledTimes(1)
    expect(result.polling.value).toBe(false)
  })

  it('404（任务已删除）立即停止，不进入退避', async () => {
    const notFound = Object.assign(new Error('Request failed with status code 404'), {
      response: { status: 404 },
    })
    const { result, refresh } = await mountPoll({ refresh: () => Promise.reject(notFound) })

    result.start()
    await vi.advanceTimersByTimeAsync(3000)
    await flushPromises()
    expect(refresh).toHaveBeenCalledTimes(1)
    expect(result.failed.value).toBe(true)
    expect(result.polling.value).toBe(false)

    await vi.advanceTimersByTimeAsync(120000)
    await flushPromises()
    expect(refresh).toHaveBeenCalledTimes(1)
  })

  it('5xx 与网络错误仍按退避重试', async () => {
    const serverError = Object.assign(new Error('Request failed with status code 500'), {
      response: { status: 500 },
    })
    const { result, refresh } = await mountPoll({ refresh: () => Promise.reject(serverError) })

    result.start()
    await vi.advanceTimersByTimeAsync(3000)
    await flushPromises()
    expect(refresh).toHaveBeenCalledTimes(1)

    await vi.advanceTimersByTimeAsync(2999)
    expect(refresh).toHaveBeenCalledTimes(1)
    await vi.advanceTimersByTimeAsync(1)
    await flushPromises()
    expect(refresh).toHaveBeenCalledTimes(2)
    expect(result.failed.value).toBe(false)
  })
})
