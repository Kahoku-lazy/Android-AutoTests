/**
 * Shared step type definitions and utilities — imported by StepEditor and StepViewer.
 */

// ── Step type definitions (17 types) ──
export const STEP_TYPES = [
  {
    value: "click",
    label: "点击元素",
    icon: "👆",
    desc: "点击屏幕上的一个元素",
    group: "元素操作",
  },
  {
    value: "long_click",
    label: "长按元素",
    icon: "🖐",
    desc: "按住元素不放，持续N秒后松开",
    group: "元素操作",
  },
  {
    value: "click_indexed",
    label: "点击第N个元素",
    icon: "👆",
    desc: "多个相同元素时，点击其中第N个",
    group: "元素操作",
  },
  {
    value: "swipe",
    label: "滑动屏幕",
    icon: "👈",
    desc: "在屏幕上向某个方向滑动一段距离",
    group: "滑动操作",
  },
  {
    value: "drag",
    label: "拖动元素",
    icon: "✋",
    desc: "按住一个元素，向某个方向拖动",
    group: "滑动操作",
  },
  {
    value: "wait",
    label: "等待元素出现",
    icon: "⏳",
    desc: "等待某个元素出现在屏幕上，超时则失败",
    group: "等待操作",
  },
  {
    value: "wait_disappear",
    label: "等待元素消失",
    icon: "⏳",
    desc: "等待某个元素从屏幕上消失，超时则失败",
    group: "等待操作",
  },
  {
    value: "wait_any",
    label: "等待任意一个出现",
    icon: "⏳",
    desc: "等待多个元素中任意一个出现即可",
    group: "等待操作",
  },
  {
    value: "wait_toast",
    label: "等待Toast消息",
    icon: "💬",
    desc: "等待系统弹出指定的Toast提示",
    group: "等待操作",
  },
  {
    value: "sleep",
    label: "暂停几秒",
    icon: "😴",
    desc: "什么都不做，暂停等待一段时间",
    group: "等待操作",
  },
  {
    value: "verify_text",
    label: "校验文字",
    icon: "✅",
    desc: "检查元素的文字内容是否等于预期值",
    group: "检查操作",
  },
  {
    value: "poll_text",
    label: "等待文字出现",
    icon: "🔄",
    desc: "等待元素出现并且文字等于预期值",
    group: "检查操作",
  },
  {
    value: "start_app",
    label: "打开应用",
    icon: "🚀",
    desc: "启动手机上的某个应用",
    group: "应用操作",
  },
  {
    value: "kill_app",
    label: "关闭应用",
    icon: "💀",
    desc: "强制退出手机上的某个应用",
    group: "应用操作",
  },
  {
    value: "restart_app",
    label: "重启应用",
    icon: "🔄",
    desc: "先关闭应用，再重新打开",
    group: "应用操作",
  },
  {
    value: "retry_click",
    label: "点击后等待结果",
    icon: "🔁",
    desc: "点击一个元素，然后等待另一个元素出现确认生效",
    group: "应用操作",
  },
  {
    value: "log",
    label: "记录信息",
    icon: "📝",
    desc: "在测试日志中记录一条文字信息",
    group: "应用操作",
  },
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
    case "click_indexed":
      return `${icon} 点击第${(step.index || 0) + 1}个「${elName}」`;
    case "swipe": {
      const dirLabel =
        DIRECTION_OPTIONS.find((d) => d.value === step.direction)?.label ||
        step.direction;
      return `${icon} 向${dirLabel}滑动 ${step.distance || 500}px`;
    }
    case "drag": {
      const dLabel =
        DIRECTION_OPTIONS.find((d) => d.value === step.direction)?.label ||
        step.direction;
      return `${icon} 拖动「${elName}」向${dLabel} ${step.distance || 500}px`;
    }
    case "wait":
      return `${icon} 等待「${elName}」出现（${step.timeout || 10}s）`;
    case "wait_disappear":
      return `${icon} 等待「${elName}」消失`;
    case "wait_any":
      return `${icon} 等待任意一个出现（${step.timeout || 10}s）`;
    case "wait_toast":
      return `${icon} 等待Toast「${step.expected_text || "?"}」`;
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
    case "restart_app":
      return `${icon} 重启应用 ${step.xpath || ""}`;
    case "retry_click":
      return `${icon} 点击「${elName}」→ 等待结果（最多${step.index || 5}次）`;
    case "log":
      return `${icon} ${step.description || "记录信息"}`;
    default:
      return `${icon} ${def?.label || step.type}`;
  }
}
