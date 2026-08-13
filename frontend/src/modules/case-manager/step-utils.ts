/**
 * 步骤显示工具 — StepViewer 使用。
 *
 * 步骤类型定义已迁移至后端 models/step_types.py::STEP_TYPE_META。
 * 前端通过 GET /api/cases/step-types?target=xxx 拉取。
 * 此文件仅保留 stepSummary() 显示逻辑和 icon 映射。
 */

// ── icon 映射（仅用于显示）──
const STEP_ICONS = {
  click: "👆", long_click: "👇", swipe: "👈", wait: "⏳", wait_disappear: "⌛",
  sleep: "💤", screenshot: "📸",
  verify_text: "✅", adb_poll_text: "🔄",
  adb_start_app: "🚀", adb_kill_app: "💀",
  adb_perf_element_time: "⏱️", adb_wait_toast: "💬",
  adb_if_appear: "🔀", adb_if_disappear: "🔀", adb_loop_n: "🔁", adb_loop_elements: "📋",
  api_request: "🌐", api_assert: "✅", api_sleep: "😴", api_log: "📝",
  web_navigate: "🔗", web_fill: "⌨️", web_type: "⌨️",
  web_wait: "⏳", web_assert: "✅", web_screenshot: "📸",
  web_click: "👆", web_step: "⚙️",
};

// ── 旧名 → 新名归一化（过渡期兼容）──
const _TYPE_ALIAS = {
  start_app: "adb_start_app", kill_app: "adb_kill_app", wait_toast: "adb_wait_toast",
  perf_element_time: "adb_perf_element_time", poll_text: "adb_poll_text",
  if_element_appear: "adb_if_appear", if_element_disappear: "adb_if_disappear",
  loop_n: "adb_loop_n", loop_elements: "adb_loop_elements",
  web_click: "click", web_screenshot: "screenshot",
};

// ── Field labels ──
export const FIELD_LABELS = {
  xpath: "目标元素",
  xpath2: "确认元素",
  timeout: "超时(秒)",
  expected_text: "预期文本",
  index: "索引",
  description: "描述",
  direction: "方向",
  distance: "距离(像素)",
  // Web / API
  selector: "CSS 选择器",
  value: "输入值",
  url: "请求 URL",
  method: "HTTP 方法",
  assertions: "断言规则",
  headers: "请求头",
  body: "请求体",
};

// ── Direction options ──
export const DIRECTION_OPTIONS = [
  { value: "up", label: "向上" },
  { value: "down", label: "向下" },
  { value: "left", label: "向左" },
  { value: "right", label: "向右" },
];

/** Resolve a human-readable element name from a step. */
export function resolveElementName(step, field = "xpath") {
  const cached = step[`_el_${field}`];
  if (cached)
    return (
      cached.alias || cached.text_val || cached.resource_id || "未命名元素"
    );
  const id = step[`_el_id_${field}`];
  if (id) return `#${id}`;
  return step.description || step[field] || "元素";
}

/** Generate a one-line Chinese step summary with emoji icon.
 *  @param {Function} [resolveFn] — optional custom element name resolver (e.g. live lookup from element library) */
export function stepSummary(step, resolveFn) {
  const type = _TYPE_ALIAS[step.type] || step.type;
  const icon = STEP_ICONS[type] || "";
  const resolve = resolveFn || resolveElementName;
  const elName = resolve(step, "xpath");

  switch (type) {
    case "click":
      return `${icon} 点击「${elName}」`;
    case "long_click":
      return `${icon} 长按「${elName}」${step.timeout || 0.8}s`;
    case "swipe": {
      const dirLabel =
        DIRECTION_OPTIONS.find((d) => d.value === step.direction)?.label ||
        step.direction;
      return `${icon} 向${dirLabel}滑动 ${step.distance || 500}px`;
    }
    case "wait":
      return `${icon} 等待「${elName}」出现（${step.timeout || 10}s）`;
    case "wait_disappear":
      return `${icon} 等待「${elName}」消失`;
    case "sleep":
      return `${icon} 暂停 ${step.timeout || 0}s`;
    case "verify_text":
      return `${icon} 检查「${elName}」文字是否="${step.expected_text || "?"}"`;
    case "poll_text":
      return `${icon} 等待「${elName}」出现，文字="${step.expected_text || "?"}"`;
    case "adb_start_app":
      return `${icon} 打开应用 ${step.xpath || ""}`;
    case "adb_kill_app":
      return `${icon} 关闭应用 ${step.xpath || ""}`;
    case "adb_perf_element_time":
      return `${icon} 等待「${elName}」出现耗时（超时${step.timeout || 10}s）`;
    case "adb_wait_toast":
      return `${icon} 等待Toast「${step.expected_text || "?"}」`;
    case "adb_if_appear":
      return `${icon} 如果「${elName}」出现 (${(step.children || []).length} 子步骤)`;
    case "adb_if_disappear":
      return `${icon} 如果「${elName}」消失 (${(step.children || []).length} 子步骤)`;
    case "adb_loop_n":
      return `${icon} 循环 ${step.index || 1} 次 (${(step.children || []).length} 子步骤)`;
    case "adb_loop_elements":
      return `${icon} 遍历 ${(step.xpath || '').split('|').filter(Boolean).length || 0} 个元素 (${(step.children || []).length} 子步骤)`;
    case "adb_poll_text":
      return `${icon} 等待「${elName}」出现，文字="${step.expected_text || "?"}"`;
    // ── API ──
    case "api_request":
      return `${icon} ${step.method || 'GET'} ${step.url || step.xpath || ''}`;
    case "api_assert":
      return `${icon} 断言: ${step.description || JSON.stringify(step.assertions || []).slice(0, 80)}`;
    case "api_sleep":
      return `${icon} 暂停 ${step.timeout || 0}s`;
    case "api_log":
      return `${icon} 日志: ${step.description || step.value || ''}`;
    // ── Web ──
    case "web_navigate":
      return `${icon} 跳转 ${step.url || ''}`;
    case "web_click":
      return `${icon} 点击「${step.selector || step.description || '元素'}」`;
    case "web_fill":
      return `${icon} 填充「${step.selector || ''}」= "${step.value || ''}"`;
    case "web_type":
      return `${icon} 逐字输入「${step.selector || ''}」= "${step.value || ''}"`;
    case "web_wait":
      return `${icon} 等待 ${step.timeout || 0}s${step.selector ? ` (${step.selector})` : ''}`;
    case "web_assert":
      return `${icon} 验证「${step.expected_text || step.description || ''}」`;
    case "web_screenshot":
      return `${icon} 截图: ${step.description || step.value || 'page'}`;
    case "web_step":
      return `${icon} ${step.description || 'Web 步骤'}`;
    default:
      return `${icon} ${step.type}`;
  }
}
