/**
 * [P0] 知识库助手文字方式 — 方式文案、状态文案与发送门控。
 */
import { describe, expect, it } from "vitest"
import { canSendText, modeLabel, statusTextFor } from "@/modules/knowledge-assistant/helpers/mode"
import { applyServerEvent } from "@/modules/knowledge-assistant/helpers/transcript"

describe("[P0] 会话方式文案", () => {
  it("语音与文字各有自己的模式名", () => {
    expect(modeLabel("voice")).toBe("语音问答")
    expect(modeLabel("text")).toBe("文字问答")
  })

  it("文字方式不说「聆听中」", () => {
    expect(statusTextFor("text", "listening")).toBe("等待提问")
    expect(statusTextFor("text", "speaking")).toBe("正在回答…")
    expect(statusTextFor("voice", "listening")).toBe("聆听中，请直接说话")
  })
})

describe("[P0] 文字发送门控", () => {
  it("只有文字方式且已连接才可发送", () => {
    expect(canSendText("voice", true, "listening")).toBe(false)
    expect(canSendText("text", false, "listening")).toBe(false)
    expect(canSendText("text", true, "listening")).toBe(true)
  })

  it("回答进行中不可再发", () => {
    expect(canSendText("text", true, "thinking")).toBe(false)
    expect(canSendText("text", true, "speaking")).toBe(false)
  })
})

describe("[P0] 文字会话消息归并", () => {
  it("服务端回显的用户消息直接收敛为完成态", () => {
    const opened = applyServerEvent(
      [],
      { type: "reply_start", reply_id: "text-a1", role: "user", name: "user" },
      1,
    )
    const echoed = applyServerEvent(
      opened,
      { type: "transcript_final", reply_id: "text-a1", role: "user", text: "长按3秒会怎样" },
      2,
    )

    expect(opened).toHaveLength(1)
    expect(opened[0].role).toBe("user")
    expect(echoed[0].text).toBe("长按3秒会怎样")
    expect(echoed[0].status).toBe("done")
  })
})
