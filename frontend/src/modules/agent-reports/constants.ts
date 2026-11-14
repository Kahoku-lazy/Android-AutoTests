/** 执行报告模块常量 — 文案与取值的唯一真相源 */

/** 页面头 */
export const REPORTS_PAGE_TITLE = "执行报告"
export const REPORTS_PAGE_SUBTITLE = "平台 UI 执行智能体每次运行的 HTML 报告，点击即可查看"
export const REPORTS_PAGE_ICON = "file-bar-chart"
export const REPORTS_PAGE_GRADIENT = "linear-gradient(135deg,var(--c-report),var(--c-ai))"

/** 列表条数上限 */
export const REPORTS_LIMIT = 50

/** 三态文案 */
export const REPORTS_EMPTY_TEXT = "还没有执行报告"
export const REPORTS_EMPTY_HINT = "运行一次平台 UI 执行任务后，报告会出现在这里"
export const REPORTS_ERROR_TEXT = "加载执行报告失败"
export const REPORTS_OPEN_ERROR_TEXT = "打开报告失败"

/** 操作文案 */
export const REPORTS_REFRESH_LABEL = "刷新"
export const REPORTS_OPEN_LABEL = "查看报告"
export const REPORTS_LOADING_LABEL = "打开中…"

/** 微倾轮转（按序号取，避免整页卡片一个角度） */
export const REPORTS_TILT_STEPS = [-0.6, 0.4, -0.3, 0.6, -0.5, 0.3] as const
