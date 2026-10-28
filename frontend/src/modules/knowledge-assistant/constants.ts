/**
 * 知识库助手模块常量：文案、路由、WS 路径、状态映射。
 *
 * 组件内不散写魔法字符串；新增文案先登记在这里。
 */
import type { VoiceState } from "./types"

export const KB_ROUTE_PATH = "/knowledge-assistant"
export const KB_WS_PATH = "/ws/knowledge-assistant/"
export const KB_PAGE_TITLE = "知识库助手"
export const KB_PAGE_SUBTITLE = "语音问答 · 对话实时写入本地日志"
export const KB_PAGE_SUBTITLE_TRANSLATE = "实时翻译 · 对话实时写入本地日志"
export const KB_PAGE_SUBTITLE_PIPELINE = "ASR + DeepSeek Flash + TTS · 对话实时写入本地日志"
export const KB_MODE_LIVETRANSLATE = "实时翻译"
export const KB_MODE_OMNI = "语音问答"
export const KB_MODE_PIPELINE = "ASR + DeepSeek + TTS"

export const KB_ROUTE_OPTIONS = [
  {
    value: "omni",
    label: "Omni 直连 · qwen3.5-omni-plus-realtime · Tina",
  },
  {
    value: "pipeline",
    label: "ASR + DeepSeek Flash + TTS",
  },
] as const

export type KbRoute = (typeof KB_ROUTE_OPTIONS)[number]["value"]
export const KB_PAGE_ICON = "book-open"
export const KB_ICON_GRADIENT = "linear-gradient(135deg,var(--c-element),var(--c-ai))"

export const KB_INPUT_SAMPLE_RATE = 16000
export const KB_OUTPUT_SAMPLE_RATE = 24000
export const KB_CAPTURE_CHUNK_MS = 100
export const KB_PLAYOUT_REPORT_MS = 200

export const KB_STATUS_TEXT: Record<VoiceState, string> = {
  idle: "未开始",
  connecting: "正在连接语音服务…",
  listening: "聆听中，请直接说话",
  thinking: "正在思考…",
  speaking: "正在回答，开口可打断",
  error: "会话出错",
}

export const KB_HINT_TEXT =
  "点击语音按键开始对话；助手回答时开口即可打断。建议戴耳机，避免外放回声。"

export const KB_EMPTY_TITLE = "还没有对话"
export const KB_EMPTY_HINT = "点击左侧语音按键，说一句话开始"

export const KB_ROLE_USER = "你"
export const KB_ROLE_ASSISTANT = "知识库助手"
export const KB_MSG_RECOGNIZING = "识别中"
export const KB_MSG_ANSWERING = "回答中"
export const KB_MSG_INTERRUPTED = "已打断"
export const KB_MSG_ERROR = "出错"
export const KB_MSG_PLACEHOLDER = "…"

export const KB_START_LABEL = "开始对话"
export const KB_STOP_LABEL = "结束对话"
export const KB_INTERRUPT_LABEL = "打断回答"

export const KB_READY_FALLBACK = "语音服务未就绪"
export const KB_STATUS_LOAD_ERROR = "无法读取知识库助手状态"
export const KB_MIC_ERROR = "无法使用麦克风，请检查浏览器权限"
export const KB_UNAUTHORIZED_ERROR = "登录已过期，请重新登录"
export const KB_SOCKET_ERROR = "语音连接已断开，请重新开始"

export const KB_MIC_IDLE = "麦克风：未采集到音频"
export const KB_MIC_WAITING = "麦克风：有信号，等待说话"
export const KB_MIC_ACTIVE = "麦克风：有输入"
export const KB_MIC_TEXT = "麦克风：未使用（文本提问）"
