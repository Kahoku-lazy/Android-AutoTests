export const NAV_CATEGORIES = [
  {
    key: "main",
    label: "",
    items: [{ path: "/dashboard", icon: "layout-dashboard", label: "仪表盘" }],
  },
  {
    key: "data",
    label: "数据",
    items: [
      { path: "/devices", icon: "smartphone", label: "设备管理" },
      { path: "/inspector", icon: "search", label: "设备检查器" },
      { path: "/elements", icon: "crosshair", label: "元素定位" },
      { path: "/workflow", icon: "git-branch", label: "页面流" },
    ],
  },
  {
    key: "ai-tasks",
    label: "AI任务",
    items: [
      { path: "/cases", icon: "layers", label: "用例管理" },
      { path: "/reports", icon: "file-bar-chart", label: "测试报告" },
    ],
  },
  {
    key: "ai-tools",
    label: "AI助手",
    items: [
      {
        path: "/ai-assistant",
        icon: "bot",
        label: "AI 助手",
        children: [
          { path: "/ai-assistant/agents", icon: "sticky-note", label: "平台小助手" },
          { path: "/ai-assistant/toolbox", icon: "wrench", label: "AI工具箱" },
          { path: "/ai-assistant/knowledge", icon: "book-open", label: "知识库" },
          { path: "/ai-assistant/evaluator", icon: "activity", label: "评测中心" },
        ],
      },
    ],
  },
]

// ── Doodle Craft 协调：path → 模块色（active 书签条），与主区 8 模块色同源 ──
export const MOD_COLORS = {
  "/dashboard": "var(--c-dashboard)",
  "/devices": "var(--c-device)",
  "/inspector": "var(--c-device)",
  "/elements": "var(--c-element)",
  "/elements/projects": "var(--c-element)",
  "/cases": "var(--c-case)",
  "/reports": "var(--c-report)",
  "/ai-assistant": "var(--c-ai)",
  "/ai-assistant/agents": "var(--c-ai)",
  "/ai-assistant/toolbox": "var(--c-ai)",
  "/ai-assistant/knowledge": "var(--c-ai)",
  "/ai-assistant/evaluator": "var(--c-ai)",
  "/workflow": "var(--c-workflow)",
}
