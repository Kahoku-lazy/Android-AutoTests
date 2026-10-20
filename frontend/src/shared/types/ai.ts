/** AI 助手模块共享类型 — 智能体、线路配置、工具与任务发布 DTO */

// ── 字面量联合类型 ──

export type AgentStatus = "active" | "paused" | "error"

// ── Agent ──
export interface AgentRecord {
  id: number
  name: string
  status: AgentStatus
  model_name?: string
  model_provider?: string
  strong_model_name?: string
  strong_enabled?: boolean
  available_models?: string[]
  tags?: string[]
  description?: string
  avatar_url?: string
  avatar?: string
  tool_count?: number
  route_configs?: RouteConfigMap
}

// ── 多线路模型配置 ──
export interface RouteModelConfig {
  provider?: string
  model_name?: string
  api_key?: string
  base_url?: string
}

export interface RouteConfig {
  name?: string
  avatar?: string
  planner?: RouteModelConfig
  executor?: RouteModelConfig
  verifier?: RouteModelConfig
}

export interface RouteConfigMap {
  device_control?: RouteConfig
}

export type AgentRoute = "device_control"

// ── 任务发布 ──
export interface TaskRecord {
  id: number
  title: string
  goal: string
  status: string
  result?: string
  device_serial?: string
  /** 卡片展示用设备名（型号）；空则前端回退 serial */
  device_label?: string
  /** 指定用例标题；空串/缺省=全部用例 */
  case_title?: string
  /** 当前线路助手名（实时派生，随改名同步） */
  assistant_name?: string
  /** 附件原始文件名（仅文件名，正文只在详情下发） */
  attachment_filename?: string
  /** 全部附件文件名；列表不下发正文 */
  attachment_names?: string[]
  created_at?: string
  started_at?: string
  finished_at?: string
  deepseek_cost?: number
}

export interface TaskSubmitPayload {
  title: string
  agent_id: number
  device_serial: string
  case_title?: string
}

export interface TaskListResponse {
  status?: boolean
  data?: { tasks: TaskRecord[] }
  message?: string
}

export interface TaskFailedItem {
  item?: string
  reason?: string
  action?: string
  assert?: string
  actual?: string
}

/** 规划步骤：一步一操作 + 一步一断言 */
export interface TaskRunStep {
  action: string
  assert: string
}

export interface TaskRunExecutorOut {
  result?: string
  /** 点击前的时间戳（新执行契约；存量旧记录没有该键） */
  click_timer?: string
  /** 点击后截图的相对路径（新执行契约；无截图时为空串） */
  screenshot?: string
  /** 存量旧记录：执行的操作 */
  action?: string
  /** 存量旧记录：模型写的说明文字 */
  message?: string
}

export interface TaskRunVerifierOut {
  /** 验收结论：新契约为 PASS/FAIL 字符串，存量旧记录为 boolean */
  result?: boolean | string
  /** 点击前的时间戳（新验收契约；存量旧记录没有该键） */
  click_timer?: string
  /** 检测到日志关键词的时间戳（新验收契约；未检测到为空串） */
  logAssertionTimer?: string
  /** 本轮检查的日志关键词（新验收契约；平台按检查工具调用自动填） */
  logAssertionInfo?: string
  /** 验证截图的相对路径（新验收契约；未取到路径为空串） */
  screenshot?: string
  /** 实际结果说明（截图里真实看到了什么） */
  actual?: string
  /** 存量旧记录：被验证的操作 */
  action?: string
  /** 存量旧记录：断言 */
  assert?: string
  summary?: string
  completed?: string[]
  failed?: TaskFailedItem[]
}

/** 设备日志证据：命中的功能点（关键词 → 功能模块 / 功能点） */
export interface TaskLogFeature {
  id?: number
  module?: string
  feature?: string
}

/** 设备日志证据：某个关键词的一次出现（那一刻的原文） */
export interface TaskLogOccurrence {
  timestamp?: string
  source?: string
  text?: string
  grade?: string
}

/** 设备日志证据：窗口原始日志行（同毫秒已合并，text 内保留换行） */
export interface TaskLogLine {
  timestamp?: string
  source?: string
  text?: string
  port?: number
}

/** 设备日志证据：某个关键词的命中块 */
export interface TaskLogEvidenceHit {
  keyword?: string
  /** strong（强证据）/ periodic（疑似周期，不能单独作为通过依据）/ before_action / out_of_window */
  grade?: string
  count?: number
  timestamps?: string[]
  occurrences?: TaskLogOccurrence[]
  features?: TaskLogFeature[]
  baseline_occurrences?: Array<{ timestamp?: string; text?: string }>
}

/** 设备日志证据：某步的验收取证块（引擎写入过程记录，页面只读展示） */
export interface TaskLogEvidence {
  channel?: string
  window_id?: string
  window_opened_at?: string
  action_time?: string
  action_times?: string[]
  threshold_seconds?: number
  baseline_seconds?: number
  window_line_count?: number
  /** hit / no_hit / no_log / out_of_window */
  conclusion?: string
  hits?: TaskLogEvidenceHit[]
  before_action?: Array<{ keyword?: string; timestamp?: string; text?: string; grade?: string }>
  out_of_window?: Array<{
    keyword?: string
    timestamp?: string
    text?: string
    grade?: string
    delta_seconds?: number
  }>
  /** 窗口原始日志（服务端已按「同毫秒合并 + 最新在上」排好，前端 MUST NOT 再排序） */
  lines?: TaskLogLine[]
}

/** 执行侧点击证据：一次副作用点击（点击前时间点 + 点击后截图路径，未截图时为空串） */
export interface TaskLogCheckClick {
  action_time?: string
  screenshot_path?: string
}

/** 执行侧点击证据块（引擎写入过程记录；log 只在「本步断言需日志核对」时非空） */
export interface TaskLogCheck {
  clicks?: TaskLogCheckClick[]
  /** 与该步验收证据同源的 5 秒窗口证据（不需日志核对的步骤为空） */
  log?: TaskLogEvidence | null
}

/** 过程日志：一步一次重试 */
export interface TaskRunLogEntry {
  action?: string
  assert?: string
  loop: number
  executor?: string | TaskRunExecutorOut
  verifier?: TaskRunVerifierOut
  /** 验收证据截图（相对 MEDIA，如 ai_tasks/12/s2_l1.jpg） */
  screenshot?: string
  /** 本步的验收设备日志证据（老任务 / 未采集时缺省） */
  log_evidence?: TaskLogEvidence
  /** 本步执行侧的点击证据（老任务 / 本步无点击且不需日志时缺省） */
  executor_log_check?: TaskLogCheck
  /** @deprecated 旧协议按目标聚合 */
  goal?: string
  steps?: Array<string | TaskRunStep>
  verification?: string
  result?: string
}

export interface TaskRunPlan {
  /** 规划输出已不再回述目标；存量记录里该键仍可能存在，故为可选 */
  goal?: string
  steps?: Array<string | TaskRunStep>
  /** @deprecated 旧协议目标级验收 */
  verification?: string
}

export interface TaskRunPayload {
  status?: string
  summary?: string
  reason?: string
  message?: string
  completed?: string[]
  failed?: TaskFailedItem[]
  plans?: TaskRunPlan[]
  log?: TaskRunLogEntry[]
  usage?: Record<string, unknown>
  models?: { planner?: string; executor?: string; verifier?: string; max_loops?: number }
  max_loops?: number
}

export interface TaskDetail {
  id: number
  title: string
  goal: string
  status: string
  device_serial?: string
  device_label?: string
  assistant_name?: string
  attachment_filename?: string
  /** 附件解析后的 Markdown 正文全文；无附件为空串 */
  attachment?: string
  /** 引擎实际交给规划模型的四键 JSON 原文（与装配同源派生） */
  planner_input?: string
  /** 配置加载结论：配置加载成功 / 加载失败 */
  load_message?: string
  /** 配置 YAML 原文 */
  yaml_body?: string
  /** 文档附件的解析正文 */
  documents?: { filename: string; body: string }[]
  created_at?: string
  started_at?: string
  finished_at?: string
  input_tokens?: number
  output_tokens?: number
  cache_input_tokens?: number
  model_usage?: Record<
    string,
    { input_tokens?: number; output_tokens?: number; cache_input_tokens?: number }
  >
  deepseek_cost?: number
  run?: TaskRunPayload
}

export interface TaskDetailResponse {
  status?: boolean
  data?: TaskDetail
  message?: string
}

export interface TaskDeleteResponse {
  status?: boolean
  message?: string
}

export interface TaskSubmitResponse {
  status?: boolean
  data?: { id?: number; status?: string; result?: string }
  message?: string
}

// ── API 响应（宽松 interface — strict:false 下字面量判别属性会被拓宽，union 窄化失效）
// Agents 组（Batch 1 已迁 DRF）：信封 {status, data}。
export interface AgentListResponse {
  status?: boolean
  data?: { agents: AgentRecord[] }
  message?: string
}

export interface AgentDetailResponse {
  status?: boolean
  data?: { agent: AgentRecord }
  message?: string
}

export interface AgentOpResponse {
  status?: boolean
  data?: { id?: number }
  message?: string
}
