/**
 * 步骤字段定义 — 前端渲染 StepEditor 表单所需。
 *
 * STEP_TYPES 已迁移至后端 models/step_types.py::STEP_TYPE_META。
 * 前端通过 GET /api/cases/step-types?target=xxx 拉取可用步骤类型。
 * 此文件仅保留前端渲染所需的字段定义和标签。
 */

export const APP_LIFECYCLE_TYPES = ['adb_start_app', 'adb_kill_app']

export const STEP_FIELDS = {
  click:             { required: ['xpath'], optional: ['timeout', 'description'] },
  long_click:        { required: ['xpath'], optional: ['timeout', 'description'] },
  swipe:             { required: ['direction'], optional: ['distance', 'description'] },
  wait:              { required: ['xpath'], optional: ['timeout', 'description'] },
  wait_disappear:    { required: ['xpath'], optional: ['timeout', 'description'] },
  sleep:             { required: ['timeout'], optional: ['description'] },
  screenshot:        { required: [], optional: ['description'] },
  verify_text:       { required: ['xpath', 'expected_text'], optional: ['timeout', 'description'] },
  adb_start_app:     { required: ['xpath'], optional: ['description'] },
  adb_kill_app:      { required: ['xpath'], optional: ['description'] },
  adb_wait_toast:    { required: ['expected_text'], optional: ['timeout', 'description'] },
  adb_perf_element_time: { required: ['xpath'], optional: ['timeout', 'description'] },
  adb_if_appear:     { required: ['xpath'], optional: ['timeout', 'description'] },
  adb_if_disappear:  { required: ['xpath'], optional: ['timeout', 'description'] },
  adb_loop_n:        { required: ['index'], optional: ['description'] },
  adb_loop_elements: { required: ['xpath'], optional: ['index', 'description'] },
  adb_poll_text:     { required: ['xpath', 'expected_text'], optional: ['timeout', 'description'] },
  web_navigate:      { required: ['url'], optional: ['description'] },
  web_fill:          { required: ['selector', 'value'], optional: ['description'] },
  web_type:          { required: ['selector', 'value'], optional: ['description'] },
  web_wait:          { required: [], optional: ['selector', 'timeout', 'description'] },
  web_assert:        { required: ['expected_text'], optional: ['timeout', 'description'] },
  // ── API ──
  api_request:       { required: ['method', 'url'], optional: ['headers', 'body', 'extract', 'expected_status', 'description'] },
  api_assert:        { required: ['assertions'], optional: ['expected_status', 'description'] },
  api_sleep:         { required: ['timeout'], optional: ['description'] },
  api_log:           { required: ['value'], optional: ['description'] },
}

export const FIELD_LABELS = {
  xpath: 'XPath 定位', xpath2: '备选 XPath', timeout: '超时（秒）',
  expected_text: '期望文本', direction: '方向', distance: '距离（像素）',
  index: '索引', description: '描述',
  selector: 'CSS 选择器', url: 'URL', value: '输入值',
  method: 'HTTP 方法', headers: '请求头 (JSON)', body: '请求体 (JSON)',
  extract: '变量提取', assertions: '断言规则', expected_status: '预期状态码',
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
  index: '循环次数或轮询间隔',
  description: '步骤描述（显示在报告）',
  selector: 'CSS 选择器，如 #login-btn / .menu-item / input[name="email"]',
  url: '目标 URL，支持 {{var}} 变量引用',
  value: '要填充的文本内容',
  method: 'HTTP 方法：GET / POST / PUT / DELETE / PATCH',
  headers: '请求头 JSON 对象，支持 {{var}}',
  body: '请求体 JSON 对象，支持 {{var}}',
  extract: '从响应中提取变量：{"变量名": "$.json.path"}',
  assertions: '断言规则列表：[{path, op, expect}]',
  expected_status: '预期 HTTP 状态码（如 200、401）',
}
