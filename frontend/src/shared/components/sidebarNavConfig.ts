export const NAV_CATEGORIES = [
  {
    key: "main",
    label: "",
    items: [{ path: "/dashboard", icon: "layout-dashboard", label: "仪表盘" }],
  },
  {
    key: "test-flow",
    items: [
      { path: "/devices", icon: "smartphone", label: "设备管理" },
      { path: "/inspector", icon: "search", label: "设备检查器" },
      {
        path: "/elements",
        icon: "crosshair",
        label: "元素定位",
        children: [
          { path: "/elements/android", icon: "smartphone", label: "Android元素管理" },
          { path: "/elements/web", icon: "globe", label: "Web端元素" },
          { path: "/elements/api", icon: "server", label: "API接口" },
        ],
      },
      { path: "/workflow", icon: "git-branch", label: "工作流工作台" },
      {
        path: "/cases",
        icon: "layers",
        label: "用例管理",
        children: [
          { path: "/cases/ui", icon: "smartphone", label: "Android UI 自动化用例" },
          { path: "/cases/web", icon: "globe", label: "Web 自动化测试用例" },
          { path: "/cases/storage", icon: "package", label: "业务功能用例" },
          { path: "/cases/api", icon: "server", label: "API 接口用例" },
        ],
      },
      { path: "/runner", icon: "play-circle", label: "执行引擎" },
      { path: "/reports", icon: "file-bar-chart", label: "测试报告" },
    ],
  },
  {
    key: "ai-tools",
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
  "/elements/android": "var(--c-element)",
  "/elements/web": "var(--c-element)",
  "/elements/api": "var(--c-element)",
  "/cases": "var(--c-case)",
  "/cases/ui": "var(--c-case)",
  "/cases/web": "var(--c-case)",
  "/cases/storage": "var(--c-case)",
  "/cases/api": "var(--c-case)",
  "/runner": "var(--c-runner)",
  "/reports": "var(--c-report)",
  "/ai-assistant": "var(--c-ai)",
  "/ai-assistant/agents": "var(--c-ai)",
  "/ai-assistant/toolbox": "var(--c-ai)",
  "/ai-assistant/knowledge": "var(--c-ai)",
  "/ai-assistant/evaluator": "var(--c-ai)",
  "/workflow": "var(--c-workflow)",
}
