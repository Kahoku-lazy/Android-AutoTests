/**
 * test-runner 模块常量 — 执行引擎
 *
 * 提取自 index.vue 和 composables/，避免魔法值散落。
 */

// ── Tab 定义 ──
export const DEFAULT_TAB = 'running'

export const TAB_KEYS = {
  ALL: 'all',
  RUNNING: 'running',
  WAITING: 'waiting',
  COMPLETED: 'completed',
  INCOMPLETE: 'incomplete',
}

export const TAB_BASE_LABELS = {
  [TAB_KEYS.ALL]: '📋 全部',
  [TAB_KEYS.RUNNING]: '⚡ 执行中',
  [TAB_KEYS.WAITING]: '⏳ 等待中',
  [TAB_KEYS.COMPLETED]: '✅ 已完成',
  [TAB_KEYS.INCOMPLETE]: '⏹ 未完成',
}

// ── 任务状态 ──
export const TASK_STATUS = {
  IDLE: 'idle',
  RUNNING: 'running',
  QUEUED: 'queued',
  DONE: 'done',
}

// ── 任务结果/结局 ──
export const TASK_OUTCOME = {
  COMPLETED: 'completed',
  STOPPED: 'stopped',
  INTERRUPTED: 'interrupted',
  ERROR: 'error',
}

/** 终态结局（任务不再变化的结束状态） */
export const TERMINAL_OUTCOMES = [
  TASK_OUTCOME.COMPLETED,
  TASK_OUTCOME.STOPPED,
  TASK_OUTCOME.INTERRUPTED,
  TASK_OUTCOME.message,
]

// ── 执行模式 ──
export const EXECUTION_MODES = {
  NOW: 'now',
  SCHEDULED: 'scheduled',
}

// ── 设备状态 ──
export const DEVICE_STATUS = {
  ONLINE: 'ONLINE',
  BUSY: 'BUSY',
}

// ── 表单默认值 ──
export const DEFAULT_FORM = {
  name: '',
  deviceSerial: '',
  caseIds: [],
  loopCount: 3,
  intervalSeconds: 5,
  mode: EXECUTION_MODES.NOW,
}

// ── 表单字段边界 ──
export const FORM_BOUNDS = {
  NAME_MAX_LENGTH: 30,
  LOOP_COUNT_MIN: 1,
  LOOP_COUNT_MAX: 10000,
  INTERVAL_MIN: 5,
  INTERVAL_MAX: 300,
}

// ── 定时与阈值 ──
export const POLL_INTERVAL = 1500          // 轮询间隔 (ms)
export const SAVE_DEBOUNCE = 1000          // 防抖保存 (ms)
export const LOG_MAX_ENTRIES = 500         // 日志最大条数
export const LOG_RETAIN_COUNT = 300        // 日志截断保留条数
export const TASK_ID_PAD_WIDTH = 3         // 任务 ID 补零宽度

// ── WebSocket 消息类型 ──
export const WS_MESSAGE_TYPES = [
  'log',
  'heartbeat',
  'case_started',
  'step_started',
  'step_result',
  'iteration_result',
  'case_finished',
  'run_finished',
  'device_error',
]

// ── 步骤执行结果 ──
export const STEP_RESULT = {
  RUNNING: 'running',
  PASS: 'pass',
  STOPPED: 'stopped',
  DONE: 'done',
}

// ── 用例步骤字段 ──
export const CASE_STEP_FIELDS = {
  STEPS_DATA: 'steps_data',
  STEPS_JSON: 'steps_json',
  TYPE: 'type',
  XPATH: 'xpath',
  DESCRIPTION: 'description',
  EXPECTED_TEXT: 'expected_text',
}

// ── 对话框尺寸 ──
export const DIALOG_WIDTH = '520px'
export const FORM_LABEL_WIDTH = '88px'
export const INPUT_FIELD_WIDTH = '160px'

// ── 前端路由 ──
export const ROUTES = {
  taskDetail: (id) => `/runner/task/${id}`,
  taskReport: (id) => `/reports/task/${encodeURIComponent(id)}`,
}

// ── 提示消息 ──
export const MESSAGES = {
  noDevices: '暂无在线设备，请先在设备管理中连接设备',
  noDeviceHint: '暂无在线设备，请先在「设备管理」中连接',
  noCases: '暂无可用用例，请先在测试用例中创建用例',
  nameRequired: '请输入任务名称',
  selectDevice: '请选择执行设备',
  selectCase: '请至少选择一个测试用例',
  intervalMin: '轮间间隔最小为 5 秒，请重新设置',
  taskCreated: (name) => `任务「${name}」已创建`,
  queuedMsg: '设备正忙，任务已加入队列，设备空闲后自动执行',
  deviceUnavailable: '设备不可用或未就绪，任务已保存，可在列表中重试',
  roundCreated: (name, round) => `已创建新任务「${name}」第${round}轮`,
}
