/**
 * 自定义 SVG 图标库 — Android-AutoTests
 * 24 个图标覆盖：设备管理、测试执行、元素定位、AI 助手、报告、用例等场景
 * 使用 Vue 3 defineComponent + h() 渲染函数，确保跨构建工具兼容
 */
import { defineComponent, h } from 'vue'

function makeIcon(name, d, opts: { fill?: string; viewBox?: string; strokeW?: number } = {}) {
  const { fill = 'none', viewBox = '0 0 24 24', strokeW = 1.8 } = opts
  return defineComponent({
    name,
    props: {
      size: { type: [Number, String], default: 24 },
      color: { type: String, default: 'currentColor' },
      className: { type: String, default: '' },
    },
    setup(props) {
      return () => h('svg', {
        width: props.size,
        height: props.size,
        class: props.className,
        viewBox,
        fill,
        stroke: props.color,
        'stroke-width': strokeW,
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
        innerHTML: d,
      })
    },
  })
}

// ─── 仪表盘 & 系统 ───
export const IconDashboard = makeIcon('IconDashboard',
  '<rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/>')

export const IconActivity = makeIcon('IconActivity',
  '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>')

export const IconMonitor = makeIcon('IconMonitor',
  '<rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/><polyline points="6 11 9 8 12 12 15 9 18 11"/>')

export const IconClipboardCheck = makeIcon('IconClipboardCheck',
  '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1"/><polyline points="9 13 11 15 15 11"/>')

export const IconSettings = makeIcon('IconSettings',
  '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>')

// ─── 设备管理 ───
export const IconDevice = makeIcon('IconDevice',
  '<rect x="5" y="2" width="14" height="20" rx="2.5"/><line x1="12" y1="18" x2="12" y2="18.01"/>')

export const IconDeviceMultiple = makeIcon('IconDeviceMultiple',
  '<rect x="1" y="4" width="15" height="18" rx="2"/><line x1="8.5" y1="18" x2="8.5" y2="18.01"/><rect x="14" y="1" width="9" height="14" rx="2"/><line x1="18.5" y1="11" x2="18.5" y2="11.01"/>')

// ─── 测试执行 ───
export const IconPlay = makeIcon('IconPlay',
  '<polygon points="5 3 19 12 5 21 5 3"/>',
  { fill: 'currentColor', strokeW: 0 })

export const IconTestTube = makeIcon('IconTestTube',
  '<path d="M14.5 2v17.5c0 1.4-1.1 2.5-2.5 2.5s-2.5-1.1-2.5-2.5V2"/><path d="M8.5 2h7"/><path d="M14.5 8h-5"/>')

export const IconCheckCircle = makeIcon('IconCheckCircle',
  '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>')

export const IconXCircle = makeIcon('IconXCircle',
  '<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>')

// ─── 元素定位 ───
export const IconTarget = makeIcon('IconTarget',
  '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>')

export const IconScan = makeIcon('IconScan',
  '<path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><line x1="7" y1="12" x2="17" y2="12"/>')

// ─── 用例管理 ───
export const IconFileCode = makeIcon('IconFileCode',
  '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><polyline points="10 13 8 15 10 17"/><polyline points="15 13 17 15 15 17"/>')

export const IconLayers = makeIcon('IconLayers',
  '<polygon points="12 2 22 8.5 12 15 2 8.5 12 2"/><polyline points="2 15.5 12 22 22 15.5"/>')

// ─── AI 助手 ───
export const IconBrain = makeIcon('IconBrain',
  '<path d="M12 4a3 3 0 0 0-3-3 2.8 2.8 0 0 0-2.2 1.3A2.7 2.7 0 0 0 5 4a3 3 0 1 0 0 6 2.7 2.7 0 0 0 1.8-1.3A2.8 2.8 0 0 0 9 10a3 3 0 0 0 3-3"/><path d="M12 4a3 3 0 0 1 3-3 2.8 2.8 0 0 1 2.2 1.3A2.7 2.7 0 0 1 19 4a3 3 0 1 1 0 6 2.7 2.7 0 0 1-1.8-1.3A2.8 2.8 0 0 1 15 10a3 3 0 0 1-3-3"/><path d="M9 10v4a3 3 0 0 0 3 3 3 3 0 0 0 3-3v-4"/><path d="M9 14h6"/>')

export const IconMessageCircle = makeIcon('IconMessageCircle',
  '<path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>')

export const IconPaperclip = makeIcon('IconPaperclip',
  '<path d="M21.4 11.6 12 21a5.2 5.2 0 0 1-7.4-7.4l10.1-10.1a3.5 3.5 0 0 1 4.9 4.9L9.5 18.5a1.8 1.8 0 0 1-2.6-2.6l9.4-9.4"/>')

export const IconImage = makeIcon('IconImage',
  '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/>')

// ─── 报告 ───
export const IconBarChart = makeIcon('IconBarChart',
  '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/><line x1="2" y1="20" x2="22" y2="20"/>')

export const IconTrendingUp = makeIcon('IconTrendingUp',
  '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>')

// ─── 快捷操作 ───
export const IconPlus = makeIcon('IconPlus',
  '<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>',
  { strokeW: 2 })

export const IconRefresh = makeIcon('IconRefresh',
  '<polyline points="1 4 1 10 7 10"/><polyline points="23 20 23 14 17 14"/><path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/>')

export const IconChevronUp = makeIcon('IconChevronUp',
  '<polyline points="18 15 12 9 6 15"/>')

export const IconChevronDown = makeIcon('IconChevronDown',
  '<polyline points="6 9 12 15 18 9"/>')

export const IconTrash = makeIcon('IconTrash',
  '<polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/>')

export const IconSearch = makeIcon('IconSearch',
  '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>')

export const IconClose = makeIcon('IconClose',
  '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>')

export const IconCheck = makeIcon('IconCheck',
  '<polyline points="20 6 9 17 4 12"/>')

export const IconGripVertical = makeIcon('IconGripVertical',
  '<circle cx="9" cy="5" r="1.5" fill="currentColor" stroke="none"/><circle cx="15" cy="5" r="1.5" fill="currentColor" stroke="none"/><circle cx="9" cy="12" r="1.5" fill="currentColor" stroke="none"/><circle cx="15" cy="12" r="1.5" fill="currentColor" stroke="none"/><circle cx="9" cy="19" r="1.5" fill="currentColor" stroke="none"/><circle cx="15" cy="19" r="1.5" fill="currentColor" stroke="none"/>')

export const IconClock = makeIcon('IconClock',
  '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>')

export const IconZap = makeIcon('IconZap',
  '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>')

// ─── 状态指示 ───
export const IconWifi = makeIcon('IconWifi',
  '<path d="M5 12.55a11 11 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><circle cx="12" cy="20" r="1"/>')

export const IconAlertCircle = makeIcon('IconAlertCircle',
  '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>')

// ─── 图表数据 ───
export const IconPieChart = makeIcon('IconPieChart',
  '<path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/>')

// ─── 账号/密码 ───
export const IconUser = makeIcon('IconUser',
  '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
  { strokeW: 1.8 })

export const IconLock = makeIcon('IconLock',
  '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M12 11V7a4 4 0 0 0-4-4v0a4 4 0 0 0-4 4v4"/>',
  { strokeW: 1.8 })

export const IconMail = makeIcon('IconMail',
  '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 4-10 8L2 4"/>',
  { strokeW: 2 })

// ─── 导航 & 发送 ───
export const IconArrowLeft = makeIcon('IconArrowLeft',
  '<line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/>',
  { strokeW: 2 })

export const IconSend = makeIcon('IconSend',
  '<line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>',
  { fill: 'currentColor', strokeW: 0 })

export const IconSave = makeIcon('IconSave',
  '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/>')

export const IconEdit = makeIcon('IconEdit',
  '<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>')
