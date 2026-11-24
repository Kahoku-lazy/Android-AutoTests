/**
 * 自定义 SVG 图标库 — Android-AutoTests
 * 15 个图标，均为当前页面在用的图标（已按全站引用核对；未引用的 30 个于
 * prune-frontend-dead-code 清退）。侧栏导航图标走 sidebarNavConfig.ts 的
 * lucide 字符串键，与本文具无关。
 * 使用 Vue 3 defineComponent + h() 渲染函数，确保跨构建工具兼容
 */
import { defineComponent, h } from "vue"

function makeIcon(name, d, opts: { fill?: string; viewBox?: string; strokeW?: number } = {}) {
  const { fill = "none", viewBox = "0 0 24 24", strokeW = 1.8 } = opts
  return defineComponent({
    name,
    props: {
      size: { type: [Number, String], default: 24 },
      color: { type: String, default: "currentColor" },
      className: { type: String, default: "" },
    },
    setup(props) {
      return () =>
        h("svg", {
          "width": props.size,
          "height": props.size,
          "class": props.className,
          viewBox,
          fill,
          "stroke": props.color,
          "stroke-width": strokeW,
          "stroke-linecap": "round",
          "stroke-linejoin": "round",
          "innerHTML": d,
        })
    },
  })
}

// ─── 仪表盘 ───
export const IconActivity = makeIcon(
  "IconActivity",
  '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
)

export const IconMonitor = makeIcon(
  "IconMonitor",
  '<rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/><polyline points="6 11 9 8 12 12 15 9 18 11"/>',
)

export const IconTrendingUp = makeIcon(
  "IconTrendingUp",
  '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>',
)

// ─── 设备管理 ───
export const IconDevice = makeIcon(
  "IconDevice",
  '<rect x="5" y="2" width="14" height="20" rx="2.5"/><line x1="12" y1="18" x2="12" y2="18.01"/>',
)

export const IconWifi = makeIcon(
  "IconWifi",
  '<path d="M5 12.55a11 11 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><circle cx="12" cy="20" r="1"/>',
)

export const IconRefresh = makeIcon(
  "IconRefresh",
  '<polyline points="1 4 1 10 7 10"/><polyline points="23 20 23 14 17 14"/><path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/>',
)

export const IconSearch = makeIcon(
  "IconSearch",
  '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',
)

// ─── 测试执行 / 任务 ───
export const IconPlay = makeIcon("IconPlay", '<polygon points="5 3 19 12 5 21 5 3"/>', {
  fill: "currentColor",
  strokeW: 0,
})

export const IconClock = makeIcon(
  "IconClock",
  '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
)

export const IconLayers = makeIcon(
  "IconLayers",
  '<polygon points="12 2 22 8.5 12 15 2 8.5 12 2"/><polyline points="2 15.5 12 22 22 15.5"/>',
)

// ─── AI 助手 ───
export const IconBrain = makeIcon(
  "IconBrain",
  '<path d="M12 4a3 3 0 0 0-3-3 2.8 2.8 0 0 0-2.2 1.3A2.7 2.7 0 0 0 5 4a3 3 0 1 0 0 6 2.7 2.7 0 0 0 1.8-1.3A2.8 2.8 0 0 0 9 10a3 3 0 0 0 3-3"/><path d="M12 4a3 3 0 0 1 3-3 2.8 2.8 0 0 1 2.2 1.3A2.7 2.7 0 0 1 19 4a3 3 0 1 1 0 6 2.7 2.7 0 0 1-1.8-1.3A2.8 2.8 0 0 1 15 10a3 3 0 0 1-3-3"/><path d="M9 10v4a3 3 0 0 0 3 3 3 3 0 0 0 3-3v-4"/><path d="M9 14h6"/>',
)

// ─── 状态指示 ───
export const IconAlertCircle = makeIcon(
  "IconAlertCircle",
  '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>',
)

// ─── 账号/密码 ───
export const IconUser = makeIcon(
  "IconUser",
  '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
  { strokeW: 1.8 },
)

export const IconLock = makeIcon(
  "IconLock",
  '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M12 11V7a4 4 0 0 0-4-4v0a4 4 0 0 0-4 4v4"/>',
  { strokeW: 1.8 },
)

export const IconMail = makeIcon(
  "IconMail",
  '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 4-10 8L2 4"/>',
  { strokeW: 2 },
)
