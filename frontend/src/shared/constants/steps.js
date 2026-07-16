/**
 * Step type definitions and field metadata — shared by StepEditor.vue and
 * the backend adapter for 14 device-control step types.
 */

export const STEP_TYPES = [
  // ── 点击操作 ──
  { value: 'click', label: '点击', icon: '👆', desc: '点击匹配的单个 UI 元素', group: '点击' },
  { value: 'click_indexed', label: '索引点击', icon: '👆', desc: '点击 XPath 匹配列表中的第 N 个', group: '点击' },
  { value: 'retry_click', label: '重试点击', icon: '🔄', desc: '元素未出现时自动等待重试', group: '点击' },
  { value: 'long_click', label: '长按', icon: '👇', desc: '长按指定元素', group: '点击' },
  // ── 等待操作 ──
  { value: 'wait', label: '等待出现', icon: '⏳', desc: '等待指定元素出现', group: '等待' },
  { value: 'wait_disappear', label: '等待消失', icon: '⌛', desc: '等待元素从屏幕消失', group: '等待' },
  { value: 'wait_any', label: '等待任一', icon: '🎯', desc: '等待两个候选元素之一出现', group: '等待' },
  { value: 'wait_toast', label: '等待 Toast', icon: '🔔', desc: '等待 Toast 消息弹出', group: '等待' },
  // ── 验证操作 ──
  { value: 'verify_text', label: '验证文本', icon: '✅', desc: '校验元素文本是否匹配期望值', group: '验证' },
  { value: 'poll_text', label: '轮询文本', icon: '📊', desc: '轮询元素文本变化并返回', group: '验证' },
  // ── 应用控制 ──
  { value: 'start_app', label: '启动 App', icon: '▶️', desc: '启动目标 App（package name）', group: '应用' },
  { value: 'kill_app', label: '停止 App', icon: '⏹', desc: '强制停止目标 App', group: '应用' },
  { value: 'restart_app', label: '重启 App', icon: '🔄', desc: '先 kill 再 start', group: '应用' },
  // ── 工具步骤 ──
  { value: 'sleep', label: '暂停', icon: '💤', desc: '固定时长暂停（秒）', group: '工具' },
  { value: 'log', label: '记录', icon: '📝', desc: '插入一条文本日志', group: '工具' },
  { value: 'swipe', label: '滑动', icon: '👈', desc: '按方向滑动指定距离', group: '工具' },
]

export const APP_LIFECYCLE_TYPES = ['start_app', 'kill_app', 'restart_app']

export const STEP_FIELDS = {
  click:             { required: ['xpath'], optional: ['timeout', 'description'] },
  click_indexed:     { required: ['xpath', 'index'], optional: ['timeout', 'description'] },
  retry_click:       { required: ['xpath'], optional: ['max_retries', 'timeout', 'description'] },
  long_click:        { required: ['xpath'], optional: ['timeout', 'description'] },
  wait:              { required: ['xpath'], optional: ['timeout', 'description'] },
  wait_disappear:    { required: ['xpath'], optional: ['timeout', 'description'] },
  wait_any:          { required: ['xpath', 'xpath2'], optional: ['timeout', 'description'] },
  wait_toast:        { optional: ['expected_text', 'timeout', 'description'] },
  verify_text:       { required: ['xpath', 'expected_text'], optional: ['timeout', 'description'] },
  poll_text:         { required: ['xpath'], optional: ['timeout', 'description'] },
  start_app:         { required: ['xpath'], optional: ['description'] },
  kill_app:          { required: ['xpath'], optional: ['description'] },
  restart_app:       { required: ['xpath'], optional: ['description'] },
  sleep:             { required: ['timeout'], optional: ['description'] },
  log:               { required: ['description'] },
  swipe:             { required: ['direction'], optional: ['distance', 'description'] },
}

export const FIELD_LABELS = {
  xpath: 'XPath 定位', xpath2: '备选 XPath', timeout: '超时（秒）',
  expected_text: '期望文本', direction: '方向', distance: '距离（像素）',
  index: '索引', max_retries: '最大重试', description: '描述',
}

export const DIRECTION_OPTIONS = [
  { value: 'up', label: '⬆ 上滑' }, { value: 'down', label: '⬇ 下滑' },
  { value: 'left', label: '⬅ 左滑' }, { value: 'right', label: '➡ 右滑' },
]

export const FIELD_HINTS = {
  xpath: '元素 XPath 定位表达式',
  xpath2: 'wait_any 第二个候选 XPath',
  timeout: '默认 10 秒',
  expected_text: '元素应包含的文本',
  direction: '滑动方向',
  distance: '默认 500 像素',
  index: '匹配列表中的索引（从 0 开始）',
  max_retries: '默认 3 次',
  description: '步骤描述（显示在报告）',
}
