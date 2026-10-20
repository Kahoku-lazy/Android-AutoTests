export const NAV_CATEGORIES = [
  {
    key: "main",
    label: "",
    items: [
      { path: "/dashboard", icon: "layout-dashboard", label: "仪表盘" },
      { path: "/ai-assistant", icon: "bot", label: "AI 助手" },
    ],
  },
  {
    key: "data",
    label: "数据",
    items: [
      { path: "/devices", icon: "smartphone", label: "设备管理" },
      { path: "/workflow", icon: "git-branch", label: "页面流" },
      { path: "/serial-log", icon: "terminal", label: "串口日志" },
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
]

// ── Doodle Craft 协调：path → 模块色（active 书签条），与主区模块色同源 ──
export const MOD_COLORS = {
  "/dashboard": "var(--c-dashboard)",
  "/devices": "var(--c-device)",
  "/cases": "var(--c-case)",
  "/reports": "var(--c-report)",
  "/ai-assistant": "var(--c-ai)",
  "/ai-assistant/agents": "var(--c-ai)",
  "/workflow": "var(--c-workflow)",
  "/serial-log": "var(--c-device)",
}
