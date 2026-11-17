/**
 * lucide 运行时图标子集（data-lucide 名 → 图标数据）
 *
 * 为什么不 import 整个 lucide：全量 1834 个图标（源码约 906 KB）会全部打进入口包；
 * 平台实际只用到下面这 20 个名字，来源两处：
 *   1. shared/components/sidebarNavConfig.ts 的 icon 字段（侧栏 14 个）
 *   2. 各页 WorkbenchHeader 的 icon 属性（含 PAGE_HEADER.icon）
 *
 * 新增图标名时在这里补一行；漏登记不会静默 —— lucide 自己会打印
 * "icon name was not found in the provided icons object" 告警。
 *
 * 末尾两个（UsersAdmin / ModelChip）是**自绘**图标，不是 lucide 的：
 * 侧栏原来写 users / cpu 却没登记，方块里空着。自绘比直接补 lucide 的通用图形更贴主题，
 * 但网格（24）、线宽（2）、圆头圆角与 lucide 保持一致，混在列表里看不出两套语言。
 *
 * 注：本项目自绘图标系统在 shared/icons/index.ts（makeIcon），与本文件的 IconNode 写法是另一套，
 * 二者都产出 24 网格描边图标；导航图标走本文件（模板里只写 data-lucide 名，不用引组件）。
 */
import {
  Activity,
  BookOpen,
  Bot,
  Bug,
  ClipboardList,
  Crosshair,
  FileBarChart,
  GitBranch,
  Layers,
  LayoutDashboard,
  Mic,
  Search,
  Settings,
  Smartphone,
  Square,
  StickyNote,
  Terminal,
  Wrench,
} from "lucide"

/** lucide 的图标节点形状：`[标签, 属性]` 序列；自绘图标按同一形状书写。 */
type IconNode = [string, Record<string, string | number>][]

/** 自绘：用户管理（一大一小两个人头 + 各自后肩），比 lucide users 更偏手写。 */
const UsersAdmin: IconNode = [
  ["circle", { cx: 9.5, cy: 7.6, r: 3.3 }],
  ["path", { d: "M3.4 20.2c0-3.1 2.8-5.3 6.1-5.3s6.1 2.2 6.1 5.3" }],
  ["path", { d: "M16.3 4.9a3.2 3.2 0 0 1 0 6.3" }],
  ["path", { d: "M18.5 14.9c2.1.7 3.3 2.4 3.3 4.6" }],
]

/** 自绘：模型配置（芯片本体 + 中间裸片 + 八根引脚）。 */
const ModelChip: IconNode = [
  ["rect", { x: 6.4, y: 6.4, width: 11.2, height: 11.2, rx: 2.2 }],
  ["rect", { x: 10.2, y: 10.2, width: 3.6, height: 3.6, rx: 0.8 }],
  ["path", { d: "M9.2 3.1v3.3" }],
  ["path", { d: "M14.8 3.1v3.3" }],
  ["path", { d: "M9.2 17.6v3.3" }],
  ["path", { d: "M14.8 17.6v3.3" }],
  ["path", { d: "M3.1 9.2h3.3" }],
  ["path", { d: "M3.1 14.8h3.3" }],
  ["path", { d: "M17.6 9.2h3.3" }],
  ["path", { d: "M17.6 14.8h3.3" }],
]

/** lucide 按 PascalCase 查表：data-lucide="layout-dashboard" → LayoutDashboard */
export const lucideIconSubset = {
  Activity,
  BookOpen,
  Bot,
  Bug,
  ClipboardList,
  Crosshair,
  FileBarChart,
  GitBranch,
  Layers,
  LayoutDashboard,
  Mic,
  Search,
  Settings,
  Smartphone,
  Square,
  StickyNote,
  Terminal,
  Wrench,
  UsersAdmin,
  ModelChip,
}
