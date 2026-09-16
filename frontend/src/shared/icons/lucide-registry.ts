/**
 * lucide 运行时图标子集（data-lucide 名 → 图标数据）
 *
 * 为什么不 import 整个 lucide：全量 1834 个图标（源码约 906 KB）会全部打进入口包；
 * 平台实际只用到下面这 14 个名字，来源两处：
 *   1. shared/components/sidebarNavConfig.ts 的 icon 字段（侧栏 12 个）
 *   2. 各页 WorkbenchHeader 的 icon 属性（含 PAGE_HEADER.icon）
 *
 * 新增图标名时在这里补一行；漏登记不会静默 —— lucide 自己会打印
 * "icon name was not found in the provided icons object" 告警。
 *
 * 注：本项目自绘图标系统在 shared/icons/index.ts（makeIcon），与本文件无关。
 */
import {
  Activity,
  BookOpen,
  Bot,
  ClipboardList,
  Crosshair,
  FileBarChart,
  GitBranch,
  Layers,
  LayoutDashboard,
  Search,
  Settings,
  Smartphone,
  StickyNote,
  Wrench,
} from 'lucide'

/** lucide 按 PascalCase 查表：data-lucide="layout-dashboard" → LayoutDashboard */
export const lucideIconSubset = {
  Activity,
  BookOpen,
  Bot,
  ClipboardList,
  Crosshair,
  FileBarChart,
  GitBranch,
  Layers,
  LayoutDashboard,
  Search,
  Settings,
  Smartphone,
  StickyNote,
  Wrench,
}
