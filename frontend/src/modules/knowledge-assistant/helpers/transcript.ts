/**
 * 对话消息 reducer：把服务端事件归并为屏幕上的消息列表。
 *
 * 纯函数、无副作用；组件只负责渲染，方便在 jsdom 下直接单测。
 */
import type { MessageStatus, ServerEvent, TranscriptMessage } from "../types"

function upsert(
  messages: TranscriptMessage[],
  id: string,
  role: TranscriptMessage["role"],
  now: number,
): TranscriptMessage[] {
  if (messages.some((message) => message.id === id)) return messages
  return [...messages, { id, role, text: "", status: "streaming", at: now }]
}

function patch(
  messages: TranscriptMessage[],
  id: string,
  changes: Partial<TranscriptMessage>,
): TranscriptMessage[] {
  return messages.map((message) => (message.id === id ? { ...message, ...changes } : message))
}

function statusForReason(reason: string): MessageStatus {
  if (reason === "interrupted") return "interrupted"
  if (reason === "error") return "error"
  return "done"
}

/**
 * 按一条服务端事件更新消息列表。
 *
 * Args:
 *   messages: 当前消息列表。
 *   event: 服务端 WS 事件。
 *   now: 新消息的时间戳（测试注入）。
 *
 * Returns:
 *   新数组；不认识的事件原样返回。
 */
export function applyServerEvent(
  messages: TranscriptMessage[],
  event: ServerEvent,
  now = Date.now(),
): TranscriptMessage[] {
  switch (event.type) {
    case "reply_start":
      return upsert(messages, event.reply_id, event.role, now)

    case "transcript_delta": {
      const withMessage = upsert(messages, event.reply_id, event.role, now)
      return patch(withMessage, event.reply_id, {
        text: `${withMessage.find((message) => message.id === event.reply_id)?.text ?? ""}${event.delta}`,
        status: "streaming",
      })
    }

    case "transcript_final": {
      const withMessage = upsert(messages, event.reply_id, event.role, now)
      return patch(withMessage, event.reply_id, {
        text: event.text,
        status: event.text.trim() ? "done" : "streaming",
      })
    }

    case "reply_end": {
      const target = messages.find((message) => message.id === event.reply_id)
      if (!target) return messages
      if (!target.text.trim()) {
        // 用户转写可能晚于 reply_end 到达：保留占位，等 transcript_final 收敛；
        // 助手没有文本则直接移除，避免留下空气泡。
        if (target.role === "user") return messages
        return messages.filter((message) => message.id !== event.reply_id)
      }
      return patch(messages, event.reply_id, {
        status: statusForReason(event.reason),
      })
    }

    default:
      return messages
  }
}
