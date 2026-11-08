/**
 * 会话方式的纯函数：方式文案、状态文案与文字发送门控。
 *
 * 组件只调用这些函数，模板里不写方式分支细节，便于在 jsdom 下直接单测。
 */
import {
  KB_MODE_TEXT,
  KB_MODE_TEXT_LABEL,
  KB_MODE_VOICE_LABEL,
  KB_STATUS_TEXT,
  KB_STATUS_TEXT_TEXT,
} from "../constants"
import type { AssistantMode, VoiceState } from "../types"

/**
 * 当前方式的展示名。
 *
 * Args:
 *   mode: 语音或文字。
 *
 * Returns:
 *   「语音问答」或「文字问答」。
 */
export function modeLabel(mode: AssistantMode): string {
  return mode === KB_MODE_TEXT ? KB_MODE_TEXT_LABEL : KB_MODE_VOICE_LABEL
}

/**
 * 当前方式在某个状态下的可读文案。
 *
 * Args:
 *   mode: 语音或文字。
 *   state: 会话状态。
 *
 * Returns:
 *   该方式对应的中文状态文案。
 */
export function statusTextFor(mode: AssistantMode, state: VoiceState): string {
  const table = mode === KB_MODE_TEXT ? KB_STATUS_TEXT_TEXT : KB_STATUS_TEXT
  return table[state]
}

/**
 * 文字输入框是否可发送：只在文字方式、且没有回答进行中时为真。
 *
 * 「是否已连接」不再是前提——未连接时发送会自动建连并把这条文本补发出去。
 *
 * Args:
 *   mode: 语音或文字。
 *   state: 会话状态。
 *
 * Returns:
 *   可发送则 true。
 */
export function canSendText(mode: AssistantMode, state: VoiceState): boolean {
  if (mode !== KB_MODE_TEXT) return false
  return state !== "thinking" && state !== "speaking"
}
