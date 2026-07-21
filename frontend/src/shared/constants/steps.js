/**
 * Step type definitions and field metadata — shared by StepEditor.vue and
 * the backend adapter for 10 device-control step types.
 */

export const STEP_TYPES = [
  // ── 点击操作 ──
  { value: 'click', label: '点击', icon: '👆', desc: '点击匹配的单个 UI 元素', group: '点击' },
  { value: 'long_click', label: '长按', icon: '👇', desc: '长按指定元素', group: '点击' },
  // ── 滑动操作 ──
  { value: 'swipe', label: '滑动', icon: '👈', desc: '按方向滑动指定距离', group: '滑动' },
  // ── 等待操作 ──
  { value: 'wait', label: '等待出现', icon: '⏳', desc: '等待指定元素出现', group: '等待' },
  { value: 'wait_disappear', label: '等待消失', icon: '⌛', desc: '等待元素从屏幕消失', group: '等待' },
  { value: 'sleep', label: '暂停', icon: '💤', desc: '固定时长暂停（秒）', group: '等待' },
  // ── 断言操作 ──
  { value: 'verify_text', label: '验证文本', icon: '✅', desc: '校验元素文本是否匹配期望值', group: '断言' },
  { value: 'poll_text', label: '轮询文本', icon: '📊', desc: '轮询等待元素文本变为期望值（显示检测耗时）', group: '断言' },
  // ── 应用控制 ──
  { value: 'start_app', label: '启动 App', icon: '▶️', desc: '启动目标 App（package name）', group: '应用' },
  { value: 'kill_app', label: '停止 App', icon: '⏹', desc: '强制停止目标 App', group: '应用' },
  // ── APP性能 ──
  { value: 'perf_element_time', label: '等待元素出现耗时', icon: '⏱️', desc: '上一步完成后开始计时，元素出现后结束计时，超时则失败', group: 'APP性能' },
  // ── 弹窗检测 ──
  { value: 'wait_toast', label: '等待Toast', icon: '💬', desc: '等待指定文本的Toast消息出现，超时则失败', group: '弹窗' },
  // ── 流程控制 ──
  { value: 'if_element_appear', label: '如果元素出现', icon: '🔀', desc: '如果目标元素出现则执行子步骤，否则跳过', group: '流程控制', container: true },
  { value: 'if_element_disappear', label: '如果元素消失', icon: '🔀', desc: '如果目标元素消失则执行子步骤，否则跳过', group: '流程控制', container: true },
  { value: 'loop_n', label: '循环N次', icon: '🔁', desc: '重复执行子步骤N次', group: '流程控制', container: true },
  { value: 'loop_elements', label: '遍历元素列表', icon: '📋', desc: '依次点击XPath列表中的每个元素（多个用|分隔），每次点击后执行子步骤', group: '流程控制', container: true },
]

export const APP_LIFECYCLE_TYPES = ['start_app', 'kill_app']

export const STEP_FIELDS = {
  click:             { required: ['xpath'], optional: ['timeout', 'description'] },
  long_click:        { required: ['xpath'], optional: ['timeout', 'description'] },
  swipe:             { required: ['direction'], optional: ['distance', 'description'] },
  wait:              { required: ['xpath'], optional: ['timeout', 'description'] },
  wait_disappear:    { required: ['xpath'], optional: ['timeout', 'description'] },
  sleep:             { required: ['timeout'], optional: ['description'] },
  verify_text:       { required: ['xpath', 'expected_text'], optional: ['timeout', 'description'] },
  poll_text:         { required: ['xpath', 'expected_text'], optional: ['timeout', 'description'] },
  start_app:          { required: ['xpath'], optional: ['description'] },
  kill_app:           { required: ['xpath'], optional: ['description'] },
  perf_element_time:   { required: ['xpath'], optional: ['timeout', 'description'] },
  wait_toast:          { required: ['expected_text'], optional: ['timeout', 'description'] },
  if_element_appear:   { required: ['xpath'], optional: ['timeout', 'description'] },
  if_element_disappear:{ required: ['xpath'], optional: ['timeout', 'description'] },
  loop_n:              { required: ['index'], optional: ['description'] },
  loop_elements:       { required: ['xpath'], optional: ['index', 'description'] },
}

export const FIELD_LABELS = {
  xpath: 'XPath 定位', xpath2: '备选 XPath', timeout: '超时（秒）',
  expected_text: '期望文本', direction: '方向', distance: '距离（像素）',
  index: '索引', description: '描述',
}

export const DIRECTION_OPTIONS = [
  { value: 'up', label: '⬆ 上滑' }, { value: 'down', label: '⬇ 下滑' },
  { value: 'left', label: '⬅ 左滑' }, { value: 'right', label: '➡ 右滑' },
]

export const FIELD_HINTS = {
  xpath: '元素 XPath 定位表达式',
  xpath2: '备用 XPath 定位（保留字段）',
  timeout: '默认 10 秒',
  expected_text: '元素应包含的文本',
  direction: '滑动方向',
  distance: '默认 500 像素',
  index: 'wait / poll_text 的轮询间隔秒数',
  description: '步骤描述（显示在报告）',
}
