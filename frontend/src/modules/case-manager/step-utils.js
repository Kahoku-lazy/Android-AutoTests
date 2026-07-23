/**
 * Shared step type definitions and utilities — imported by StepEditor and StepViewer.
 */

// ── Step type definitions (10 types) ──
export const STEP_TYPES = [
  { value: "click", label: "点击元素", icon: "👆", desc: "点击屏幕上的一个元素", group: "点击" },
  { value: "long_click", label: "长按元素", icon: "🖐", desc: "按住元素不放，持续N秒后松开", group: "点击" },
  { value: "swipe", label: "滑动屏幕", icon: "👈", desc: "在屏幕上向某个方向滑动一段距离", group: "滑动" },
  { value: "wait", label: "等待元素出现", icon: "⏳", desc: "等待某个元素出现在屏幕上，超时则失败", group: "等待" },
  { value: "wait_disappear", label: "等待元素消失", icon: "⏳", desc: "等待某个元素从屏幕上消失，超时则失败", group: "等待" },
  { value: "sleep", label: "暂停几秒", icon: "😴", desc: "什么都不做，暂停等待一段时间", group: "等待" },
  { value: "verify_text", label: "校验文字", icon: "✅", desc: "检查元素的文字内容是否等于预期值", group: "断言" },
  { value: "poll_text", label: "等待文字出现", icon: "🔄", desc: "轮询等待元素出现并且文字等于预期值，显示检测耗时", group: "断言" },
  { value: "start_app", label: "打开应用", icon: "🚀", desc: "启动手机上的某个应用", group: "应用" },
  { value: "kill_app", label: "关闭应用", icon: "💀", desc: "强制退出手机上的某个应用", group: "应用" },
  { value: "perf_element_time", label: "等待元素出现耗时", icon: "⏱️", desc: "上一步完成后开始计时，元素出现后结束计时，超时则失败", group: "APP性能" },
  { value: "wait_toast", label: "等待Toast消息", icon: "💬", desc: "等待指定文本的Toast消息出现", group: "弹窗" },
  { value: "if_element_appear", label: "如果元素出现", icon: "🔀", desc: "如果目标元素出现则执行子步骤，否则跳过", group: "流程控制", container: true },
  { value: "if_element_disappear", label: "如果元素消失", icon: "🔀", desc: "如果目标元素消失则执行子步骤，否则跳过", group: "流程控制", container: true },
  { value: "loop_n", label: "循环N次", icon: "🔁", desc: "重复执行子步骤N次", group: "流程控制", container: true },
  { value: "loop_elements", label: "遍历元素列表", icon: "📋", desc: "依次点击XPath列表中的每个元素（多个用|分隔）", group: "流程控制", container: true },
  // ── API 请求类 ──
  { value: "api_request", label: "API 请求", icon: "🌐", desc: "发送 HTTP 请求并记录响应", group: "API 请求" },
  { value: "api_assert", label: "断言验证", icon: "✅", desc: "验证 API 响应内容是否符合预期", group: "API 请求" },
  { value: "api_sleep", label: "暂停等待", icon: "😴", desc: "暂停等待一段时间", group: "API 请求" },
  { value: "api_log", label: "输出日志", icon: "📝", desc: "输出自定义日志信息", group: "API 请求" },
  // ── Web 自动化类 ──
  { value: "web_navigate", label: "页面跳转", icon: "🔗", desc: "浏览器导航到指定 URL", group: "Web 自动化" },
  { value: "web_click", label: "点击元素", icon: "👆", desc: "点击页面上的 CSS 选择器元素", group: "Web 自动化" },
  { value: "web_fill", label: "填充输入", icon: "⌨️", desc: "向输入框填充文本", group: "Web 自动化" },
  { value: "web_type", label: "逐字输入", icon: "⌨️", desc: "逐字符输入文本（模拟真实打字）", group: "Web 自动化" },
  { value: "web_wait", label: "等待", icon: "⏳", desc: "等待元素出现或固定时间", group: "Web 自动化" },
  { value: "web_assert", label: "验证文本", icon: "✅", desc: "验证页面上存在指定文本", group: "Web 自动化" },
  { value: "web_screenshot", label: "截图", icon: "📸", desc: "截取当前页面截图", group: "Web 自动化" },
  { value: "web_step", label: "Web 步骤", icon: "⚙️", desc: "通用 Web 操作步骤", group: "Web 自动化" },
];

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

/** Generate a one-line Chinese step summary with emoji icon. */
export function stepSummary(step) {
  const def = STEP_TYPES.find((t) => t.value === step.type);
  const icon = def?.icon || "";
  const elName = resolveElementName(step, "xpath");

  switch (step.type) {
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
    case "start_app":
      return `${icon} 打开应用 ${step.xpath || ""}`;
    case "kill_app":
      return `${icon} 关闭应用 ${step.xpath || ""}`;
    case "perf_element_time":
      return `${icon} 等待「${elName}」出现耗时（超时${step.timeout || 10}s）`;
    case "wait_toast":
      return `${icon} 等待Toast「${step.expected_text || "?"}」`;
    case "if_element_appear":
      return `${icon} 如果「${elName}」出现 (${(step.children || []).length} 子步骤)`;
    case "if_element_disappear":
      return `${icon} 如果「${elName}」消失 (${(step.children || []).length} 子步骤)`;
    case "loop_n":
      return `${icon} 循环 ${step.index || 1} 次 (${(step.children || []).length} 子步骤)`;
    case "loop_elements":
      return `${icon} 遍历 ${(step.xpath || '').split('|').filter(Boolean).length || 0} 个元素 (${(step.children || []).length} 子步骤)`;
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
      return `${icon} ${def?.label || step.type}`;
  }
}
