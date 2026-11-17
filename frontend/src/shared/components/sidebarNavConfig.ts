export interface NavItem {
  path: string
  icon: string
  label: string
  /** 开发中的条目：右侧显示红色「开发中」标签 */
  isDev?: boolean
  /** 自定义标签文案（缺省「开发中」） */
  badge?: string
  badgeClass?: string
  children?: NavItem[]
}

export interface NavCategory {
  key: string
  label: string
  items: NavItem[]
  /** 仅运营/超管可见的分组：为真时按当前用户身份过滤 */
  requiresOperator?: boolean
}

export const NAV_CATEGORIES: NavCategory[] = [
  {
    key: "main",
    label: "",
    items: [{ path: "/dashboard", icon: "layout-dashboard", label: "仪表盘" }],
  },
  {
    key: "ai",
    label: "AI 功能",
    items: [
      { path: "/ai-assistant", icon: "bot", label: "AI 助手" },
      { path: "/agent-reports", icon: "clock", label: "执行报告" },
    ],
  },
  {
    key: "data",
    label: "数据",
    items: [
      { path: "/devices", icon: "smartphone", label: "设备管理" },
      { path: "/serial-log", icon: "terminal", label: "串口日志" },
    ],
  },
  {
    key: "ai-tasks",
    label: "AI任务",
    items: [
      { path: "/tasks", icon: "clipboard-list", label: "任务清单" },
      { path: "/cases", icon: "layers", label: "用例管理" },
      { path: "/reports", icon: "file-bar-chart", label: "测试报告" },
      { path: "/bugs", icon: "bug", label: "BUG单管理" },
    ],
  },
  {
    key: "ops",
    label: "运营",
    requiresOperator: true,
    items: [{ path: "/ops/users", icon: "users", label: "用户管理" }],
  },
]

// ── Doodle Craft 协调：path → 模块色（active 书签条），与主区模块色同源 ──
export const MOD_COLORS = {
  "/dashboard": "var(--c-dashboard)",
  "/devices": "var(--c-device)",
  "/tasks": "var(--c-ai)",
  "/cases": "var(--c-case)",
  "/reports": "var(--c-report)",
  "/bugs": "var(--c-runner)",
  "/ai-assistant": "var(--c-ai)",
  "/ai-assistant/agents": "var(--c-ai)",
  "/serial-log": "var(--c-device)",
  "/agent-reports": "var(--c-report)",
  "/ops/users": "var(--c-ops)",
}
