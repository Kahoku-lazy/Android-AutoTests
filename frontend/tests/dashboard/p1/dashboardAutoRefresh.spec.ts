/**
 * [P1] 建议测 — 仪表盘静默轮询（30 秒）：到点刷新、慢请求不叠加、隐藏暂停、回到可见立即刷新、卸载停止
 * 目录：tests/dashboard/p1/
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { flushPromises, mount } from "@vue/test-utils"
import { defineComponent, h, KeepAlive, nextTick, ref } from "vue"
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

/** 按 App.vue 的真实结构挂载：KeepAlive 缓存，切走只失活不卸载 */
function mountAutoKeepAlive(refresh: () => Promise<void>) {
  const visible = ref(true)
  const Comp = defineComponent({
    name: "DashboardProbe",
    setup() {
      useDashboardAutoRefresh(refresh)
      return () => h("div")
    },
  })
  const Placeholder = defineComponent({
    name: "DashboardPlaceholder",
    setup: () => () => h("span"),
  })
  const Host = defineComponent({
    setup: () => () =>
      h(KeepAlive, null, {
        default: () => (visible.value ? h(Comp, { key: "dashboard" }) : h(Placeholder, { key: "other" })),
      }),
  })
  const wrapper = mount(Host)
  return {
    wrapper,
    deactivate: async () => {
      visible.value = false
      await nextTick()
    },
    activate: async () => {
      visible.value = true
      await nextTick()
    },
  }
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

  it("离开页面（keep-alive 失活）后停止轮询，回来立即刷新一次并恢复定时器", async () => {
    const refresh = vi.fn().mockResolvedValue(undefined)
    const { wrapper, deactivate, activate } = mountAutoKeepAlive(refresh)

    // 切走后 3 个周期内不请求（页面被缓存，组件未卸载）
    await deactivate()
    vi.advanceTimersByTime(DASHBOARD_REFRESH_MS * 3)
    await nextTick()
    expect(refresh).not.toHaveBeenCalled()

    // 回到页面：立即补一次，不等 30 秒
    await activate()
    await flushPromises()
    expect(refresh).toHaveBeenCalledTimes(1)

    // 定时器已恢复
    vi.advanceTimersByTime(DASHBOARD_REFRESH_MS)
    await flushPromises()
    expect(refresh).toHaveBeenCalledTimes(2)

    wrapper.unmount()
  })
})
