/**
 * [P0] 知识库助手对话消息 reducer — 服务端事件归并。
 */
import { describe, expect, it } from "vitest"
import { applyServerEvent } from "@/modules/knowledge-assistant/helpers/transcript"
import type { TranscriptMessage } from "@/modules/knowledge-assistant/types"

const AT = 1_700_000_000_000

describe("[P0] 对话 reducer", () => {
  it("用户转写先占位、再增量、最后收敛", () => {
    let messages: TranscriptMessage[] = []

    messages = applyServerEvent(
      messages,
      { type: "reply_start", reply_id: "u1", role: "user", name: "user" },
      AT,
    )
    expect(messages).toEqual([
      { id: "u1", role: "user", text: "", status: "streaming", at: AT },
    ])

    messages = applyServerEvent(
      messages,
      { type: "transcript_delta", reply_id: "u1", role: "user", delta: "设备" },
      AT,
    )
    messages = applyServerEvent(
      messages,
      { type: "transcript_delta", reply_id: "u1", role: "user", delta: "怎么连" },
      AT,
    )
    expect(messages[0].text).toBe("设备怎么连")

    messages = applyServerEvent(
      messages,
      { type: "transcript_final", reply_id: "u1", role: "user", text: "设备怎么连" },
      AT,
    )
    expect(messages[0]).toMatchObject({
      text: "设备怎么连",
      status: "done",
    })
  })

  it("助手回复结束后为 done", () => {
    let messages: TranscriptMessage[] = []
    messages = applyServerEvent(
      messages,
      { type: "reply_start", reply_id: "a1", role: "assistant", name: "知识库助手" },
      AT,
    )
    messages = applyServerEvent(
      messages,
      { type: "transcript_delta", reply_id: "a1", role: "assistant", delta: "先打开设备管理" },
      AT,
    )
    messages = applyServerEvent(
      messages,
      { type: "transcript_final", reply_id: "a1", role: "assistant", text: "先打开设备管理" },
      AT,
    )
    messages = applyServerEvent(
      messages,
      { type: "reply_end", reply_id: "a1", role: "assistant", reason: "completed" },
      AT,
    )

    expect(messages[0]).toMatchObject({
      text: "先打开设备管理",
      status: "done",
    })
  })

  it("被打断的回复标记为 interrupted，并只保留最终前缀", () => {
    let messages: TranscriptMessage[] = []
    messages = applyServerEvent(
      messages,
      { type: "reply_start", reply_id: "a1", role: "assistant", name: "知识库助手" },
      AT,
    )
    messages = applyServerEvent(
      messages,
      { type: "transcript_delta", reply_id: "a1", role: "assistant", delta: "先打开设备管理再连接" },
      AT,
    )
    messages = applyServerEvent(
      messages,
      { type: "transcript_final", reply_id: "a1", role: "assistant", text: "先打开设备管理" },
      AT,
    )
    messages = applyServerEvent(
      messages,
      { type: "reply_end", reply_id: "a1", role: "assistant", reason: "interrupted" },
      AT,
    )

    expect(messages[0]).toMatchObject({
      text: "先打开设备管理",
      status: "interrupted",
    })
  })

  it("用户转写未到时不删除占位，助手空回复则移除", () => {
    const placeholder: TranscriptMessage[] = [
      { id: "u1", role: "user", text: "", status: "streaming", at: AT },
      { id: "a1", role: "assistant", text: "", status: "streaming", at: AT },
    ]

    const afterUser = applyServerEvent(
      placeholder,
      { type: "reply_end", reply_id: "u1", role: "user", reason: "completed" },
      AT,
    )
    expect(afterUser.some((message) => message.id === "u1")).toBe(true)

    const afterAssistant = applyServerEvent(
      afterUser,
      { type: "reply_end", reply_id: "a1", role: "assistant", reason: "completed" },
      AT,
    )
    expect(afterAssistant.some((message) => message.id === "a1")).toBe(false)
  })

  it("不改动传入数组", () => {
    const original: TranscriptMessage[] = []
    applyServerEvent(
      original,
      { type: "reply_start", reply_id: "a1", role: "assistant", name: "知识库助手" },
      AT,
    )

    expect(original).toEqual([])
  })

  it("不认识的事件原样返回", () => {
    const original: TranscriptMessage[] = []

    const messages = applyServerEvent(
      original,
      { type: "audio_item", item_id: "a1" },
      AT,
    )

    expect(messages).toBe(original)
  })
})
