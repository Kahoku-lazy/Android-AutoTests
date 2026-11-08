/**
 * [P0] 必测 — 知识库助手 WS 鉴权失败的自愈
 * 目录：tests/knowledge-assistant/p0/
 *
 * 覆盖 specs/knowledge-assistant-voice/spec.md：
 * 凭证过期的用户仍能开始对话（建连前续期）、4401 后重连一次、重连仍被拒才提示过期。
 */
import { beforeEach, describe, expect, it, vi } from "vitest"
import { flushPromises } from "@vue/test-utils"

vi.mock("@/shared/auth/token-refresh", () => ({
  ensureFreshToken: vi.fn(),
  refreshAccessToken: vi.fn(),
}))

import * as tokenRefresh from "@/shared/auth/token-refresh"
import { useAssistantSession } from "@/modules/knowledge-assistant/composables/useAssistantSession"
import { KB_UNAUTHORIZED_ERROR } from "@/modules/knowledge-assistant/constants"

class FakeWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3
  static instances: FakeWebSocket[] = []

  url: string
  readyState = FakeWebSocket.CONNECTING
  binaryType = "blob"
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: (() => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  sent: unknown[] = []

  constructor(url: string) {
    this.url = url
    FakeWebSocket.instances.push(this)
  }

  send(data: unknown): void {
    this.sent.push(data)
  }

  close(): void {
    this.readyState = FakeWebSocket.CLOSED
  }
}

/** 模拟服务端的鉴权拒绝：先发 error 帧，再以 4401 关闭 */
function rejectWith4401(socket: FakeWebSocket, message = "登录状态已过期，请刷新页面后重试"): void {
  socket.onmessage?.({ data: JSON.stringify({ type: "error", message }) } as MessageEvent)
  socket.onclose?.({ code: 4401 } as CloseEvent)
}

describe("[P0] 知识库助手 WS 鉴权自愈", () => {
  beforeEach(() => {
    FakeWebSocket.instances = []
    vi.stubGlobal("WebSocket", FakeWebSocket)
    vi.clearAllMocks()
    vi.mocked(tokenRefresh.ensureFreshToken).mockResolvedValue("fresh-access")
    vi.mocked(tokenRefresh.refreshAccessToken).mockResolvedValue("refreshed-access")
  })

  it("建连前先续期，用续期后的凭证连接", async () => {
    const session = useAssistantSession()
    await session.start("text")
    await flushPromises()

    expect(tokenRefresh.ensureFreshToken).toHaveBeenCalledTimes(1)
    expect(FakeWebSocket.instances).toHaveLength(1)
    expect(FakeWebSocket.instances[0].url).toContain("token=fresh-access")
    expect(FakeWebSocket.instances[0].url).toContain("mode=text")
  })

  it("没有可用凭证时不建连并提示过期", async () => {
    vi.mocked(tokenRefresh.ensureFreshToken).mockResolvedValue("")

    const session = useAssistantSession()
    await session.start("text")
    await flushPromises()

    expect(FakeWebSocket.instances).toHaveLength(0)
    expect(session.state.value).toBe("error")
    expect(session.errorMessage.value).toBe(KB_UNAUTHORIZED_ERROR)
  })

  it("4401 后换新凭证重连一次，页面不落错误态", async () => {
    const session = useAssistantSession()
    await session.start("text")
    await flushPromises()

    rejectWith4401(FakeWebSocket.instances[0])
    await flushPromises()

    expect(tokenRefresh.refreshAccessToken).toHaveBeenCalledTimes(1)
    expect(FakeWebSocket.instances).toHaveLength(2)
    expect(FakeWebSocket.instances[1].url).toContain("token=refreshed-access")
    expect(session.state.value).not.toBe("error")
    expect(session.errorMessage.value).toBe("")
  })

  it("重连仍被 4401 拒绝时提示过期，且不再循环", async () => {
    const session = useAssistantSession()
    await session.start("text")
    await flushPromises()

    rejectWith4401(FakeWebSocket.instances[0])
    await flushPromises()
    rejectWith4401(FakeWebSocket.instances[1])
    await flushPromises()

    expect(FakeWebSocket.instances).toHaveLength(2)
    expect(tokenRefresh.refreshAccessToken).toHaveBeenCalledTimes(1)
    expect(session.state.value).toBe("error")
    expect(session.errorMessage.value).toBe(KB_UNAUTHORIZED_ERROR)
  })
})
