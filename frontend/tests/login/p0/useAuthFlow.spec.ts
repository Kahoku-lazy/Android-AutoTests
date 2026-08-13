/**
 * [P0] 必测 — 登录/注册 API 编排（mock 后端）
 * 目录：tests/login/p0/
 *
 * 表单校验在 LoginView.logic（调用方）；本文件只测网络层与副作用。
 */
import { computed, ref } from "vue"
import { beforeEach, describe, expect, it, vi } from "vitest"
import { ElMessage } from "element-plus"
import { login, register } from "@/shared/api/auth"
import { useAuthFlow } from "@/views/composables/useAuthFlow"
import type { UseAuthPoolReturn } from "@/shared/composables/useAuthPool"
import { mountComposable } from "../../helpers/mountComposable"

vi.mock("@/shared/api/auth", () => ({
  login: vi.fn(),
  register: vi.fn(),
}))

vi.mock("element-plus", () => ({
  ElMessage: {
    warning: vi.fn(),
    success: vi.fn(),
  },
}))

function makeAuth(): UseAuthPoolReturn {
  return {
    activeAccount: ref(""),
    accountList: computed(() => []),
    loginAccount: vi.fn(),
    switchAccount: vi.fn(),
    logoutAccount: vi.fn(),
  }
}

describe("[P0] useAuthFlow", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("登录成功：写 token、记住账号、跳转 dashboard", async () => {
    vi.mocked(login).mockResolvedValue({
      status: true,
      data: {
        access_token: "a1",
        refresh_token: "r1",
      },
    } as never)

    const auth = makeAuth()
    const saveUsername = vi.fn()
    const { result, router } = await mountComposable(() => useAuthFlow({ auth, saveUsername }))
    const push = vi.spyOn(router, "push")

    await result.authenticate({
      mode: "login",
      username: "  alice  ",
      password: "secret",
    })

    expect(login).toHaveBeenCalledWith("alice", "secret")
    expect(auth.loginAccount).toHaveBeenCalledWith("alice", "a1", "r1")
    expect(saveUsername).toHaveBeenCalledWith("alice")
    expect(ElMessage.success).toHaveBeenCalled()
    expect(push).toHaveBeenCalledWith("/dashboard")
    expect(result.loading.value).toBe(false)
  })

  it("登录业务失败：写入 serverError", async () => {
    vi.mocked(login).mockResolvedValue({
      status: false,
      message: "密码错误",
    } as never)

    const auth = makeAuth()
    const { result } = await mountComposable(() => useAuthFlow({ auth, saveUsername: vi.fn() }))

    await result.authenticate({
      mode: "login",
      username: "alice",
      password: "bad",
    })

    expect(result.serverError.value).toBe("密码错误")
    expect(auth.loginAccount).not.toHaveBeenCalled()
  })

  it("登录抛错：写入 serverError", async () => {
    vi.mocked(login).mockRejectedValue({
      response: { data: { message: "服务不可用" } },
    })

    const auth = makeAuth()
    const { result } = await mountComposable(() => useAuthFlow({ auth, saveUsername: vi.fn() }))

    await result.authenticate({
      mode: "login",
      username: "alice",
      password: "secret",
    })

    expect(result.serverError.value).toBe("服务不可用")
  })

  it("注册成功：写 token，不调用 saveUsername", async () => {
    vi.mocked(register).mockResolvedValue({
      status: true,
      data: {
        access_token: "a2",
        refresh_token: "r2",
      },
    } as never)

    const auth = makeAuth()
    const saveUsername = vi.fn()
    const { result, router } = await mountComposable(() => useAuthFlow({ auth, saveUsername }))
    const push = vi.spyOn(router, "push")

    await result.authenticate({
      mode: "register",
      username: "  bob  ",
      password: "  123456  ",
      password2: "  123456  ",
      email: "  bob@example.com  ",
    })

    expect(register).toHaveBeenCalledWith("bob", "123456", "123456", "bob@example.com")
    expect(auth.loginAccount).toHaveBeenCalledWith("bob", "a2", "r2")
    expect(saveUsername).not.toHaveBeenCalled()
    expect(push).toHaveBeenCalledWith("/dashboard")
  })

  it("clearServerError 清空错误", async () => {
    const auth = makeAuth()
    const { result } = await mountComposable(() => useAuthFlow({ auth, saveUsername: vi.fn() }))
    result.serverError.value = "oops"
    result.clearServerError()
    expect(result.serverError.value).toBe("")
  })
})
