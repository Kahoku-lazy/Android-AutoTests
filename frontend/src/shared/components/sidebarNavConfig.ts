export const NAV_CATEGORIES = [
  {
    key: "main",
    label: "",
    items: [{ path: "/dashboard", icon: "layout-dashboard", label: "仪表盘" }],
  },
  {
    key: "test-flow",
    label: "测试全流程",
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
    label: "AI 与编排",
    items: [
      { path: "/ai-assistant", icon: "bot", label: "AI 助手" },
      { path: "/workflow", icon: "git-branch", label: "工作流工作台", isDev: true },
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
