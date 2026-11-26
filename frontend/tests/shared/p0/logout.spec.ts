import { describe, expect, it, vi } from "vitest"
import { runLogout } from "@/shared/helpers/logout"

function makeDeps(overrides: Partial<Parameters<typeof runLogout>[0]> = {}) {
  const calls: string[] = []
  const deps = {
    hasUnsaved: vi.fn(() => false),
    confirmDiscard: vi.fn(async () => {
      calls.push("confirm")
      return true
    }),
    revoke: vi.fn(async () => {
      calls.push("revoke")
      return undefined
    }),
    clearSession: vi.fn(() => {
      calls.push("clearSession")
    }),
    goToLogin: vi.fn(() => {
      calls.push("goToLogin")
    }),
    onRevokeError: vi.fn(),
    ...overrides,
  }
  return { deps, calls }
}

describe("[P0] 退出登录顺序", () => {
  it("没有未保存改动时不弹确认，直接吊销→清会话→回登录页", async () => {
    const { deps, calls } = makeDeps()
    await expect(runLogout(deps)).resolves.toBe(true)
    expect(deps.confirmDiscard).not.toHaveBeenCalled()
    expect(calls).toEqual(["revoke", "clearSession", "goToLogin"])
  })

  it("有未保存改动时先确认，确认后才吊销会话", async () => {
    const { deps, calls } = makeDeps({ hasUnsaved: vi.fn(() => true) })
    await expect(runLogout(deps)).resolves.toBe(true)
    expect(calls).toEqual(["confirm", "revoke", "clearSession", "goToLogin"])
  })

  it("有未保存改动且用户选择留下时什么都不做", async () => {
    const { deps, calls } = makeDeps({
      hasUnsaved: vi.fn(() => true),
      confirmDiscard: vi.fn(async () => false),
    })
    await expect(runLogout(deps)).resolves.toBe(false)
    expect(deps.revoke).not.toHaveBeenCalled()
    expect(deps.clearSession).not.toHaveBeenCalled()
    expect(deps.goToLogin).not.toHaveBeenCalled()
    expect(calls).toEqual([])
  })

  it("吊销失败仍清本地会话并回登录页，错误交给调用方提示", async () => {
    const error = { response: { status: 503, data: { retry: true } } }
    const { deps, calls } = makeDeps({ revoke: vi.fn(async () => Promise.reject(error)) })
    await expect(runLogout(deps)).resolves.toBe(true)
    expect(deps.onRevokeError).toHaveBeenCalledWith(error)
    expect(calls).toEqual(["clearSession", "goToLogin"])
  })
})
