/** 串口日志页文案与 Tab 定义（唯一真相源） */

/** 页头 */
export const SERIAL_LOG_PAGE_TITLE = "串口日志"
export const SERIAL_LOG_PAGE_SUBTITLE = "无线串口监听开关、当前日志查看与关键词对照表"
export const SERIAL_LOG_PAGE_ICON = "terminal"

export type SerialLogTabKey = "ports" | "keywords"

export interface SerialLogTabDef {
  key: SerialLogTabKey
  label: string
}

/** 两个 Tab（key 同时作为路由内状态与测试锚点） */
export const SERIAL_LOG_TABS: SerialLogTabDef[] = [
  { key: "ports", label: "无线端口" },
  { key: "keywords", label: "日志关键词" },
]

export const SERIAL_LOG_DEFAULT_TAB: SerialLogTabKey = "ports"

/** 区块头文案 */
export const PORTS_PANEL_TITLE = "无线端口"
export const PORTS_PANEL_DESC = "端口监听开关与原始日志查看"
export const KEYWORDS_PANEL_TITLE = "日志关键词"
export const KEYWORDS_PANEL_DESC = "关键词 → 功能模块 / 功能点（判定口径，只读）"

/** 无权限说明 */
export const SERIAL_LOG_READONLY_HINT = "仅超级管理员可以开关监听"

/** 日志关键词表格列 */
export const LOG_KEYWORD_SEARCH_PLACEHOLDER = "搜索关键词 / 功能模块 / 功能点…"
export const LOG_KEYWORD_COL_KEYWORD = "关键词"
export const LOG_KEYWORD_COL_MODULE = "功能模块"
export const LOG_KEYWORD_COL_FEATURE = "功能点"

/** 取值来源的中文口径（后端 origin 字段） */
export const LOG_KEYWORD_ORIGIN_LABELS: Record<string, string> = {
  runtime: "运行中的采集索引",
  file: "关键词表文件",
  none: "未取到",
}

/** 改表生效时机：判定用的是平台启动时加载的那份表 */
export const LOG_KEYWORD_RESTART_HINT = "改关键词表后需重启平台才用于判定"

export const LOG_KEYWORD_EMPTY_TEXT = "暂无可用的日志关键词"
export const LOG_KEYWORD_EMPTY_HINT =
  "关键词表文件缺失或尚未生成：检查 DEVICE_LOG_KEYWORD_FILE 指向的文件"
export const LOG_KEYWORD_NO_MATCH_TEXT = "没有匹配的关键词"
