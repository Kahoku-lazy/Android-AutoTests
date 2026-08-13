/**
 * [P0] 必测 — 设备列表心跳轮询（fake timers，不真实等待 30s）
 * 目录：tests/device-pool/p0/
 *
 * useHeartbeat：startHeartbeat 按 HEARTBEAT_INTERVAL 周期调用 tick、
 * 重复 start 不产生双定时器、组件卸载后 onUnmounted 停止轮询。
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useHeartbeat } from '@/modules/device-pool/composables/useHeartbeat'
import { HEARTBEAT_INTERVAL } from '@/modules/device-pool/constants'
import { mountComposable } from '../../helpers/mountComposable'

describe('[P0] useHeartbeat', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.clearAllTimers()
    vi.useRealTimers()
  })

  it('启动后：按 HEARTBEAT_INTERVAL 周期调用 tick', async () => {
    const tick = vi.fn().mockResolvedValue(undefined)
    const { result } = await mountComposable(() => useHeartbeat())

    result.startHeartbeat(tick)
    expect(result.heartbeatActive.value).toBe(true)

    await vi.advanceTimersByTimeAsync(HEARTBEAT_INTERVAL * 3)
    expect(tick).toHaveBeenCalledTimes(3)
  })

  it('二次 start：不产生双定时器', async () => {
    const tick = vi.fn().mockResolvedValue(undefined)
    const { result } = await mountComposable(() => useHeartbeat())

    result.startHeartbeat(tick)
    result.startHeartbeat(tick)

    await vi.advanceTimersByTimeAsync(HEARTBEAT_INTERVAL)
    expect(tick).toHaveBeenCalledTimes(1)
    expect(result.heartbeatActive.value).toBe(true)
  })

  it('unmount 后：不再调用 tick', async () => {
    const tick = vi.fn().mockResolvedValue(undefined)
    const { result, wrapper } = await mountComposable(() => useHeartbeat())

    result.startHeartbeat(tick)
    await vi.advanceTimersByTimeAsync(HEARTBEAT_INTERVAL)
    expect(tick).toHaveBeenCalledTimes(1)

    wrapper.unmount()
    expect(result.heartbeatActive.value).toBe(false)

    await vi.advanceTimersByTimeAsync(HEARTBEAT_INTERVAL * 3)
    expect(tick).toHaveBeenCalledTimes(1)
  })
})
