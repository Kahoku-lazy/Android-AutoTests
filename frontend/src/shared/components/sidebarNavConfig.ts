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
      { path: "/elements", icon: "crosshair", label: "元素定位" },
      { path: "/cases", icon: "layers", label: "用例管理" },
      { path: "/runner", icon: "play-circle", label: "执行引擎" },
      { path: "/reports", icon: "file-bar-chart", label: "测试报告" },
    ],
  },
  {
    key: "ai-tools",
    items: [
      { path: "/ai-assistant", icon: "bot", label: "AI 助手" },
      { path: "/workflow", icon: "git-branch", label: "工作流工作台" },
      {
        path: "/digital-human",
        icon: "user-round",
        label: "平台数字人",
        badge: "待开发",
        badgeClass: "sidebar-menu__badge--pending",
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
  "/cases": "var(--c-case)",
  "/runner": "var(--c-runner)",
  "/reports": "var(--c-report)",
  "/ai-assistant": "var(--c-ai)",
  "/workflow": "var(--c-workflow)",
  "/digital-human": "var(--c-ai)",
}
