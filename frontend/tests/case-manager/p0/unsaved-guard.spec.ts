import { mount } from "@vue/test-utils"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { defineComponent } from "vue"

const guardSlot = vi.hoisted(() => ({
  current: null as null | ((to: { path: string }) => unknown),
}))
const confirmMock = vi.hoisted(() => vi.fn())

vi.mock("vue-router", () => ({
  onBeforeRouteLeave: (guard: () => unknown) => {
    guardSlot.current = guard
  },
}))

vi.mock("element-plus", () => ({
  ElMessageBox: { confirm: confirmMock },
}))

import {
  confirmLeaveUnsaved,
  useUnsavedGuard,
} from "@/modules/case-manager/composables/useUnsavedGuard"
import {
  UNSAVED_LEAVE_CONFIRM,
  UNSAVED_LEAVE_MESSAGE,
  UNSAVED_LEAVE_TITLE,
} from "@/modules/case-manager/constants"

let mounted: ReturnType<typeof mount>[] = []

function mountGuard(isDirty: () => boolean, isActive?: () => boolean) {
  const Probe = defineComponent({
    setup() {
      useUnsavedGuard(isDirty, isActive)
      return () => null
    },
  })
  const wrapper = mount(Probe)
  mounted.push(wrapper)
  return wrapper
}

function fireBeforeUnload(): Event {
  const event = new Event("beforeunload", { cancelable: true })
  window.dispatchEvent(event)
  return event
}

beforeEach(() => {
  guardSlot.current = null
  confirmMock.mockReset()
})

afterEach(() => {
  for (const wrapper of mounted) wrapper.unmount()
  mounted = []
  guardSlot.current = null
})

describe("[P0] 未保存改动离开守卫", () => {
  it("没有改动时路由离开直接放行，且不弹确认", async () => {
    mountGuard(() => false)
    const guard = guardSlot.current
    expect(guard).toBeTypeOf("function")
    await expect(guard?.({ path: "/cases" })).resolves.toBe(true)
    expect(confirmMock).not.toHaveBeenCalled()
  })

  it("有改动时先弹确认，确认后放行", async () => {
    confirmMock.mockResolvedValue("confirm")
    mountGuard(() => true)
    await expect(guardSlot.current?.({ path: "/cases" })).resolves.toBe(true)
    expect(confirmMock).toHaveBeenCalledTimes(1)
    expect(confirmMock).toHaveBeenCalledWith(
      UNSAVED_LEAVE_MESSAGE,
      UNSAVED_LEAVE_TITLE,
      expect.objectContaining({ confirmButtonText: UNSAVED_LEAVE_CONFIRM }),
    )
  })

  it("有改动且用户选择留下时留在原页", async () => {
    confirmMock.mockRejectedValue("cancel")
    mountGuard(() => true)
    await expect(guardSlot.current?.({ path: "/cases" })).resolves.toBe(false)
  })

  it("confirmLeaveUnsaved 把取消映射成 false", async () => {
    confirmMock.mockRejectedValue("cancel")
    await expect(confirmLeaveUnsaved()).resolves.toBe(false)
    confirmMock.mockResolvedValue("confirm")
    await expect(confirmLeaveUnsaved()).resolves.toBe(true)
  })

  it("挂载后拦截 beforeunload，卸载后不再拦截", () => {
    const wrapper = mountGuard(() => true)
    expect(fireBeforeUnload().defaultPrevented).toBe(true)
    wrapper.unmount()
    expect(fireBeforeUnload().defaultPrevented).toBe(false)
  })

  it("没有改动时 beforeunload 不拦截", () => {
    mountGuard(() => false)
    expect(fireBeforeUnload().defaultPrevented).toBe(false)
  })

  it("跳到登录页（退出登录）直接放行，不二次确认", async () => {
    mountGuard(() => true)
    await expect(guardSlot.current?.({ path: "/login" })).resolves.toBe(true)
    expect(confirmMock).not.toHaveBeenCalled()
  })

  it("页面被 KeepAlive 缓存（非当前页）时不拦截 beforeunload", () => {
    mountGuard(
      () => true,
      () => false,
    )
    expect(fireBeforeUnload().defaultPrevented).toBe(false)
  })
})
