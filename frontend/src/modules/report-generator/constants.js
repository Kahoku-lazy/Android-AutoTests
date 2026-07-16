/**
 * report-generator 模块常量 — 测试报告
 *
 * 提取自 index.vue 和 api.js，避免魔法值散落。
 */

// ── 表格列定义 (animal-island Table API) ──
export const TABLE_COLUMNS = [
  { title: 'Run ID', dataIndex: 'run_id', width: '13%' },
  { title: '设备', dataIndex: 'device_serial', width: '9%' },
  { title: '任务名称', dataIndex: 'task_name', width: '20%' },
  { title: '创建人', dataIndex: 'creator', width: '7%' },
  { title: '用例数', dataIndex: 'case_count', width: '5%', align: 'center' },
  { title: '通过', dataIndex: 'passed', width: '5%', align: 'center' },
  { title: '失败', dataIndex: 'failed', width: '5%', align: 'center' },
  { title: '通过率', dataIndex: 'rate', width: '11%' },
  { title: '状态', dataIndex: 'status', width: '7%', align: 'center' },
  { title: '耗时', dataIndex: 'duration', width: '6%', align: 'center' },
  { title: '时间', dataIndex: 'started_at', width: '12%' },
]

// ── 分页配置 ──
export const PAGE_SIZE_OPTIONS = [10, 50, 100]

// ── 表格布局尺寸 (px) ──
export const TABLE_TOOLBAR_HEIGHT = 52
export const TABLE_HEADER_HEIGHT = 54
export const TABLE_ROW_HEIGHT = 50
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

// ── 执行状态枚举 ──
export const STATUS_KEYS = {
  ALL: 'all',
  COMPLETED: 'COMPLETED',
  FAILED: 'FAILED',
  STOPPED: 'STOPPED',
}

// ── 状态筛选 Tabs（label 不含动态计数，由 computed 拼接） ──
export const STATUS_TAB_LABELS = {
  [STATUS_KEYS.ALL]: '全部',
  [STATUS_KEYS.COMPLETED]: '已完成',
  [STATUS_KEYS.FAILED]: '失败',
  [STATUS_KEYS.STOPPED]: '已停止',
}

// ── 状态标签映射 ──
export const STATUS_LABEL_MAP = {
  COMPLETED: '通过',
  completed: '通过',
  FAILED: '失败',
  failed: '失败',
  RUNNING: '运行中',
  running: '运行中',
  STOPPED: '已停止',
  stopped: '已停止',
  PENDING: '排队中',
}

// ── 状态 CSS 类映射 ──
export const STATUS_BADGE_CLASS = {
  COMPLETED: 'badge-pass',
  completed: 'badge-pass',
  PASSED: 'badge-pass',
  FAILED: 'badge-fail',
  failed: 'badge-fail',
  RUNNING: 'badge-running',
  running: 'badge-running',
  STOPPED: 'badge-stopped',
  stopped: 'badge-stopped',
  PENDING: 'badge-stopped',
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

// ── 页面 Hero header ──
export const PAGE_HEADER = {
  title: '测试报告',
  subtitle: '查看历史测试执行记录，点击 Run ID 进入详细报告',
  mark: '📊',
}

// ── 空状态文案 ──
export const EMPTY_TEXT = {
  noData: '暂无执行记录，请先执行测试',
  noRecords: '暂无执行记录',
  hint: '请先在执行引擎中运行测试，完成后将自动生成报告',
}
