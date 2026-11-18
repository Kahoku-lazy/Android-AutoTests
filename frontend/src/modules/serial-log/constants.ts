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
export const SERIAL_LOG_READONLY_HINT = "仅超级管理员可以开关监听与新增 / 编辑 / 删除端口"

/** 本机监听地址条 */
export const PORTS_IP_LABEL = "本机监听地址"
export const PORTS_IP_COPY_LABEL = "复制 IP"
export const PORTS_IP_HINT =
  "无线串口盒 / 设备侧请填入此 IP（需与本机同局域网），端口按下表配置；平台在所有网卡上监听。"
export const PORTS_IP_EMPTY = "未探测到本机局域网 IP，可设置 DEVICE_LOG_ADVERTISE_HOST 指定"
export const PORTS_IP_COPIED = "已复制本机监听地址"
export const PORTS_IP_COPY_FAILED = "复制失败，请手动选择地址复制"

/** 端口来源徽标（后端 origin 字段） */
export const PORTS_ORIGIN_LABELS: Record<string, string> = {
  config: "配置",
  custom: "自定义",
}

/** 端口行操作与状态文案 */
export const PORTS_ADD_LABEL = "新增端口"
export const PORTS_EDIT_LABEL = "编辑"
export const PORTS_DELETE_LABEL = "删除"
export const PORTS_RETRY_LABEL = "重试"
export const PORTS_LISTEN_FAIL_LABEL = "监听失败"
export const PORTS_ADDRESS_FALLBACK = "IP 未探测到"

/** 新增 / 编辑端口弹窗 */
export const PORT_FORM_TITLE_ADD = "新增端口"
export const PORT_FORM_TITLE_EDIT = "编辑自定义端口"
export const PORT_FORM_SUB_ADD = "保存后立即开始监听；端口 / SKU / 波特率自定义，不影响其它端口。"
export const PORT_FORM_SUB_EDIT =
  "端口号不可改；改 SKU 会更换日志文件通道名，保存后自动重启该端口监听。"
export const PORT_FORM_PORT_LABEL = "端口号（1–65535）"
export const PORT_FORM_SKU_LABEL = "SKU 名称（被测设备型号，决定日志通道名）"
export const PORT_FORM_BAUD_LABEL = "波特率（串口盒侧参数，仅登记展示）"
export const PORT_FORM_BAUD_CUSTOM = "自定义…"
export const PORT_FORM_SAVE = "保存并监听"
export const PORT_FORM_SAVING = "保存中…"
export const PORT_FORM_CANCEL = "取消"
export const PORT_FORM_PORT_PLACEHOLDER = "如 7008"
export const PORT_FORM_SKU_PLACEHOLDER = "如 H717D"
export const PORT_FORM_BAUD_CUSTOM_LABEL = "自定义波特率"
export const PORT_FORM_BAUD_CUSTOM_PLACEHOLDER = "如 460800"
export const PORTS_BAUD_OPTIONS = [9600, 115200, 921600]

/** 表单校验文案 */
export const PORT_ERR_PORT_REQUIRED = "端口必填，且为 1–65535 的整数"
export const PORT_ERR_PORT_DUPLICATE = "已登记（配置或自定义），不能重复新增"
export const PORT_ERR_SKU_REQUIRED = "SKU 名称必填（决定日志通道名）"
export const PORT_ERR_SKU_TOO_LONG = "SKU 名称不能超过 100 个字符"
export const PORT_ERR_BAUD_INVALID = "波特率须为正整数"

/** 删除确认 */
export const PORT_DELETE_TITLE = "删除自定义端口"
export const PORT_DELETE_WARNING =
  "删除后停止该端口监听并移除登记，历史日志文件保留；AI 设备任务验收将不再有该端口的日志证据。"
export const PORT_DELETE_CONFIRM = "删除端口"

/** 端口表分页：固定 10 行/页（单取值不渲染选择器） */
export const PORTS_PAGE_SIZE = 10
export const PORTS_PAGE_SIZE_OPTIONS = [PORTS_PAGE_SIZE]

/** 端口表筛选与计数文案 */
export const PORTS_ONLY_LISTENING_LABEL = "只看监听中"

/** 日志关键词表格列 */
export const LOG_KEYWORD_SEARCH_PLACEHOLDER = "搜索关键词 / 功能模块 / 功能点…"
export const LOG_KEYWORD_COL_KEYWORD = "关键词"
export const LOG_KEYWORD_COL_MODULE = "功能模块"
export const LOG_KEYWORD_COL_FEATURE = "功能点"
export const LOG_KEYWORD_COL_SCOPE = "范围"

/** 范围筛选的「全部」选项文案 */
export const LOG_KEYWORD_SCOPE_ALL = "全部范围"

/** 取值来源的中文口径（后端 origin 字段） */
export const LOG_KEYWORD_ORIGIN_LABELS: Record<string, string> = {
  db: "数据库关键词表",
  none: "未取到",
}

/** 生效时机：条目取自数据库，刷新即取最新 */
export const LOG_KEYWORD_REFRESH_HINT = "刷新即取最新条目"

export const LOG_KEYWORD_EMPTY_TEXT = "暂无可用的日志关键词"
export const LOG_KEYWORD_EMPTY_HINT = "关键词表暂无条目：请经维护入口登记（sl_log_keywords）"
export const LOG_KEYWORD_NO_MATCH_TEXT = "没有匹配的关键词"
