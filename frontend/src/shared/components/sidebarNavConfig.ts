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
    // 本组不显示分组标题：入口直接跟在仪表盘之后，靠图标与组间距区分
    label: "",
    items: [{ path: "/ai-assistant", icon: "bot", label: "平台助手" }],
  },
  {
    key: "data",
    label: "数据",
    items: [
      { path: "/devices", icon: "smartphone", label: "设备管理" },
      { path: "/serial-log", icon: "terminal", label: "串口日志" },
      { path: "/knowledge-search", icon: "book-open", label: "知识库" },
    ],
  },
  {
    key: "ai-tasks",
    label: "AI任务",
    items: [
      { path: "/tasks", icon: "clipboard-list", label: "任务清单" },
      { path: "/cases", icon: "layers", label: "用例管理" },
      { path: "/bugs", icon: "bug", label: "BUG单管理" },
      { path: "/reports", icon: "file-bar-chart", label: "测试报告" },
    ],
  },
  {
    key: "ops",
    label: "运营",
    requiresOperator: true,
    items: [
      { path: "/ops/users", icon: "users-admin", label: "用户管理" },
      { path: "/ops/agents", icon: "bot", label: "Agent配置" },
      { path: "/ops/model-configs", icon: "model-chip", label: "模型配置" },
    ],
  },
]

// ── Doodle Craft 协调：path → 模块色（active 书签条 + 图标底色），与主区模块色同源 ──
// 同一分组内的入口 MUST NOT 同色：数据组的设备/串口、AI任务组的任务/用例/BUG、运营组的三项各自区分。
export const MOD_COLORS = {
  "/dashboard": "var(--c-dashboard)",
  "/devices": "var(--c-device)",
  "/tasks": "var(--c-task)",
  "/cases": "var(--c-case)",
  "/reports": "var(--c-report)",
  "/bugs": "var(--c-runner)",
  "/ai-assistant": "var(--c-ai)",
  "/serial-log": "var(--c-workflow)",
  "/knowledge-search": "var(--c-case)",
  "/ops/users": "var(--c-account)",
  "/ops/agents": "var(--c-element)",
  "/ops/model-configs": "var(--c-ops)",
}
