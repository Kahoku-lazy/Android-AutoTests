/**
 * report-generator 模块常量 — 测试报告
 *
 * 提取自 index.vue 和 api.js，避免魔法值散落。
 */

// ── 表格列定义 ──
export const TABLE_COLUMNS = [
  { title: '任务 ID', dataIndex: 'run_id', minWidth: 120 },
  { title: '设备', dataIndex: 'device_serial', minWidth: 140 },
  { title: '任务名称', dataIndex: 'task_name', minWidth: 220 },
  { title: '创建人', dataIndex: 'creator', minWidth: 100 },
  { title: '状态', dataIndex: 'status', minWidth: 100, align: 'center' },
  { title: '耗时', dataIndex: 'duration', minWidth: 90, align: 'center' },
  { title: '时间', dataIndex: 'started_at', minWidth: 150 },
]

// ── 分页配置 ──
export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100]

// ── 表格布局尺寸 (px) ──
export const TABLE_TOOLBAR_HEIGHT = 52
export const TABLE_HEADER_HEIGHT = 45
export const TABLE_ROW_HEIGHT = 41
export const TABLE_EMPTY_ROWS = 3
export const TABLE_TAB_OFFSET = 88

// ── 图表配置 ──
export const CHART_RANGE_OPTIONS = [
  { key: 7, label: '一周' },
  { key: 30, label: '一月' },
  { key: 90, label: '一季度' },
]
export const CHART_DEFAULT_RANGE = 30
export const CHART_VISIBLE_DAYS = 5
export const CHART_DEFAULT_DAY_WIDTH = 72
export const CHART_CANVAS_HEIGHT = 200

// ── 去抖延迟 (ms) ──
export const FILTER_DEBOUNCE = 350
export const CHART_RESIZE_DEBOUNCE = 150
export const CHART_RENDER_DELAY = 100

// ── 通过率阈值 ──
export const PASS_RATE_EXCELLENT = 95
export const PASS_RATE_WARNING = 80

// ── 执行状态枚举（Step 1 后端小写收敛后单口径）──
export const STATUS_KEYS = {
  ALL: 'all',
  COMPLETED: 'completed',
  FAILED: 'failed',
  STOPPED: 'stopped',
}

// ── 状态筛选 Tabs（label 不含动态计数，由 computed 拼接） ──
export const STATUS_TAB_LABELS = {
  [STATUS_KEYS.ALL]: '全部',
  [STATUS_KEYS.COMPLETED]: '已完成',
  [STATUS_KEYS.FAILED]: '失败',
  [STATUS_KEYS.STOPPED]: '已停止',
}

// ── 状态标签映射（小写口径）──
export const STATUS_LABEL_MAP = {
  completed: '通过',
  success: '通过',
  failed: '失败',
  running: '运行中',
  stopped: '已停止',
  pending: '排队中',
}

// ── 状态 CSS 类映射（小写口径）──
export const STATUS_BADGE_CLASS = {
  completed: 'badge-pass',
  success: 'badge-pass',
  passed: 'badge-pass',
  failed: 'badge-fail',
  running: 'badge-running',
  stopped: 'badge-stopped',
  pending: 'badge-stopped',
}

// ── 图表配色 ──
export const CHART_COLORS = {
  passRate: {
    line: '#19c8b9',
    fill: 'rgba(25,200,185,0.08)',
    point: '#19c8b9',
    pointBorder: '#fff',
  },
  passBar: {
    fill: 'rgba(111,186,44,0.75)',
    stroke: '#6fba2c',
  },
  failBar: {
    fill: 'rgba(224,90,90,0.75)',
    stroke: '#e05a5a',
  },
  /** 轴文字 / 轴标题 / 滑块手柄：原散落在两个图表组件 script 内的字面量，2026-09-15 集中于此（画布例外，见 frontend/AGENTS.md L4 §③.7）*/
  axis: {
    labelText: '#9f927d',
    titleText: '#725d42',
    handle: '#19c8b9',
  },
}

// ── 图表样式参数 ──
export const CHART_STYLE = {
  pointBorderWidth: 2,
  pointRadius: 4,
  pointHoverRadius: 6,
  lineBorderWidth: 2.5,
  barBorderWidth: 1.5,
  barBorderRadius: 6,
  barPercentage: 0.9,
  categoryPercentage: 0.7,
  xMaxRotation: 45,
  xMinRotation: 0,
  yMin: 0,
  yMax: 105,
  legendLabelPadding: 20,
  stepSize: 1,
  precision: 0,
}

// ── 列表动画配置 ──
export const LIST_ANIMATION = {
  opacity: [0, 1],
  translateY: [16, 0],
  staggerDelay: 40,
  duration: 380,
  ease: 'outCubic',
}

// ── 路由路径 ──
export const ROUTES = {
  reportDetail: (id) => `/reports/${encodeURIComponent(id)}`,
  caseBreakdown: (type) => `/reports/cases/${type}`,
}

// ── 页头配置 ──
// 列表页与三个详情页共用同一图标与底纹，避免同一串颜色/图标名在四处硬编码
export const REPORT_HEADER_ICON = 'file-bar-chart'
export const REPORT_HEADER_GRADIENT = 'linear-gradient(135deg,#999,#8b7f8f)'

export const PAGE_HEADER = {
  title: '测试报告',
  subtitle: '查看 AI 助手任务执行记录',
  icon: REPORT_HEADER_ICON,
  iconGradient: REPORT_HEADER_GRADIENT,
}

// ── 空状态文案 ──
export const EMPTY_TEXT = {
  noData: '暂无执行记录，请先在 AI 助手发布任务',
  noRecords: '暂无执行记录',
  hint: '请先在 AI 助手发布任务，完成后将自动出现在此列表',
}
