/**
 * [P0] 必测 — 文字方式直接发送（无需先点「开始对话」）
 * 目录：tests/knowledge-assistant/p0/
 *
 * 覆盖 specs/knowledge-assistant-text-chat/spec.md：
 * 未连接时发送 → 自动建连 → ready 后补发且只发一次；会话失败时提示且不留下待发文本。
 */
import { beforeEach, describe, expect, it, vi } from "vitest"
import { flushPromises } from "@vue/test-utils"

vi.mock("@/shared/auth/token-refresh", () => ({
  ensureFreshToken: vi.fn(),
  refreshAccessToken: vi.fn(),
}))

import * as tokenRefresh from "@/shared/auth/token-refresh"
import { useAssistantSession } from "@/modules/knowledge-assistant/composables/useAssistantSession"

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

  /** 服务端就绪帧（真实连接在收到 ready 前也已进入 OPEN） */
  ready(): void {
    this.readyState = FakeWebSocket.OPEN
    this.onmessage?.({
      data: JSON.stringify({ type: "ready", mode: "text", model: "deepseek-flash" }),
    } as MessageEvent)
  }

  /** 本连接发出的文本提问 */
  texts(): string[] {
    return this.sent
      .filter((item): item is string => typeof item === "string")
      .map((item) => JSON.parse(item) as { type: string; text?: string })
      .filter((item) => item.type === "text")
      .map((item) => item.text || "")
  }
}

describe("[P0] 文字方式直接发送", () => {
  beforeEach(() => {
    FakeWebSocket.instances = []
    vi.stubGlobal("WebSocket", FakeWebSocket)
    vi.clearAllMocks()
    vi.mocked(tokenRefresh.ensureFreshToken).mockResolvedValue("fresh-access")
  })

  it("未连接时发送会自动建连，并在 ready 后补发一次", async () => {
    const session = useAssistantSession()
    session.mode.value = "text"

    session.submitText("长按开关按键3秒会怎样？")
    await flushPromises()

    expect(FakeWebSocket.instances).toHaveLength(1)
    expect(FakeWebSocket.instances[0].url).toContain("mode=text")
    // ready 之前不发送：上行没有 text 帧
    expect(FakeWebSocket.instances[0].texts()).toEqual([])

    FakeWebSocket.instances[0].ready()
    await flushPromises()

    expect(FakeWebSocket.instances[0].texts()).toEqual(["长按开关按键3秒会怎样？"])
    expect(session.socketOpen.value).toBe(true)
  })

  it("建连前连发两条会按顺序补发，不丢也不重复", async () => {
    const session = useAssistantSession()
    session.mode.value = "text"

    session.submitText("第一句")
    session.submitText("第二句")
    await flushPromises()

    expect(FakeWebSocket.instances).toHaveLength(1)
    FakeWebSocket.instances[0].ready()
    await flushPromises()

    expect(FakeWebSocket.instances[0].texts()).toEqual(["第一句", "第二句"])
  })

  it("已连接时直接发送，不重复建连", async () => {
    const session = useAssistantSession()
    session.mode.value = "text"

    session.submitText("第一句")
    await flushPromises()
    FakeWebSocket.instances[0].ready()
    await flushPromises()

    session.submitText("第二句")
    await flushPromises()

    expect(FakeWebSocket.instances).toHaveLength(1)
    expect(FakeWebSocket.instances[0].texts()).toEqual(["第一句", "第二句"])
  })

  it("空文本不触发建连", async () => {
    const session = useAssistantSession()
    session.mode.value = "text"

    session.submitText("   ")
    await flushPromises()

    expect(FakeWebSocket.instances).toHaveLength(0)
  })

  it("语音方式不接收输入框发送", async () => {
    const session = useAssistantSession()
    session.mode.value = "voice"

    session.submitText("不该发出去")
    await flushPromises()

    expect(FakeWebSocket.instances).toHaveLength(0)
  })

  it("回答进行中不发新问题", async () => {
    const session = useAssistantSession()
    session.mode.value = "text"

    session.submitText("第一句")
    await flushPromises()
    const socket = FakeWebSocket.instances[0]
    socket.ready()
    await flushPromises()

    session.state.value = "thinking"
    session.submitText("插队的问题")
    await flushPromises()

    expect(socket.texts()).toEqual(["第一句"])
  })

  it("建连失败时提示错误，且不会把文本留到下次会话", async () => {
    vi.mocked(tokenRefresh.ensureFreshToken).mockResolvedValue("")

    const session = useAssistantSession()
    session.mode.value = "text"
    session.submitText("会被丢掉的问题")
    await flushPromises()

    expect(session.errorMessage.value).toBeTruthy()
    expect(FakeWebSocket.instances).toHaveLength(0)

    // 恢复后重新发送：不应补发上一次的问题
    vi.mocked(tokenRefresh.ensureFreshToken).mockResolvedValue("fresh-access")
    session.submitText("新的问题")
    await flushPromises()
    FakeWebSocket.instances[0].ready()
    await flushPromises()

    expect(FakeWebSocket.instances[0].texts()).toEqual(["新的问题"])
  })
})
