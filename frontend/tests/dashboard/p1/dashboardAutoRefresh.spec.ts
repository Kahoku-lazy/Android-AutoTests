/**
 * [P1] 建议测 — 仪表盘静默轮询（30 秒）：到点刷新、慢请求不叠加、隐藏暂停、回到可见立即刷新、卸载停止
 * 目录：tests/dashboard/p1/
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { mount } from "@vue/test-utils"
import { defineComponent, h, nextTick } from "vue"
import {
  DASHBOARD_REFRESH_MS,
  useDashboardAutoRefresh,
} from "@/modules/dashboard/composables/useDashboardAutoRefresh"

const hiddenDescriptor = Object.getOwnPropertyDescriptor(Document.prototype, "hidden")

function setHidden(value: boolean): void {
  Object.defineProperty(document, "hidden", {
    configurable: true,
    get: () => value,
  })
}

function mountAuto(refresh: () => Promise<void>) {
  const Comp = defineComponent({
    setup() {
      useDashboardAutoRefresh(refresh)
      return () => h("div")
    },
  })
  return mount(Comp)
}

describe("[P1] useDashboardAutoRefresh", () => {
  beforeEach(() => {
    vi.useFakeTimers()
    setHidden(false)
  })

  afterEach(() => {
    vi.useRealTimers()
    delete (document as unknown as { hidden?: boolean }).hidden
    if (hiddenDescriptor) {
      Object.defineProperty(Document.prototype, "hidden", hiddenDescriptor)
    }
  })

  it("间隔不短于 15 秒，避免比重查询还快", () => {
    expect(DASHBOARD_REFRESH_MS).toBeGreaterThanOrEqual(15_000)
  })

  it("每个周期静默刷新一次", async () => {
    const refresh = vi.fn().mockResolvedValue(undefined)
    const wrapper = mountAuto(refresh)

    vi.advanceTimersByTime(DASHBOARD_REFRESH_MS)
    await nextTick()

    expect(refresh).toHaveBeenCalledTimes(1)
    wrapper.unmount()
  })

  it("上一轮未返回时跳过下一轮，不叠加慢请求", async () => {
    let release: (() => void) | null = null
    const refresh = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          release = resolve
        }),
    )
    const wrapper = mountAuto(refresh)

    vi.advanceTimersByTime(DASHBOARD_REFRESH_MS)
    await nextTick()
    vi.advanceTimersByTime(DASHBOARD_REFRESH_MS * 2)
    await nextTick()

    expect(refresh).toHaveBeenCalledTimes(1)

    release?.()
    await nextTick()
    vi.advanceTimersByTime(DASHBOARD_REFRESH_MS)
    await nextTick()

    expect(refresh).toHaveBeenCalledTimes(2)
    wrapper.unmount()
  })

  it("页面隐藏时跳过本轮", async () => {
    const refresh = vi.fn().mockResolvedValue(undefined)
    const wrapper = mountAuto(refresh)
    setHidden(true)

    vi.advanceTimersByTime(DASHBOARD_REFRESH_MS * 2)
    await nextTick()

    expect(refresh).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it("回到可见时立即刷新，不等下一个周期", async () => {
    const refresh = vi.fn().mockResolvedValue(undefined)
    const wrapper = mountAuto(refresh)
    setHidden(true)
    vi.advanceTimersByTime(DASHBOARD_REFRESH_MS)
    await nextTick()
    expect(refresh).not.toHaveBeenCalled()

    setHidden(false)
    document.dispatchEvent(new Event("visibilitychange"))
    await nextTick()

    expect(refresh).toHaveBeenCalledTimes(1)
    wrapper.unmount()
  })

  it("卸载后清理定时器，不再请求", async () => {
    const refresh = vi.fn().mockResolvedValue(undefined)
    const wrapper = mountAuto(refresh)
    wrapper.unmount()

    vi.advanceTimersByTime(DASHBOARD_REFRESH_MS * 3)
    await nextTick()

    expect(refresh).not.toHaveBeenCalled()
  })
})
