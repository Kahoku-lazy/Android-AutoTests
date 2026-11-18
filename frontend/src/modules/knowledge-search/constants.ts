/** 知识库检索页常量：文案与默认值唯一真相源。 */

export const KS_PAGE_TITLE = "知识库"
export const KS_PAGE_ICON = "book-open"

/** 三态文案：no_hit 与 unavailable 必须不同（引擎红线 7）。 */
export const KS_NO_HIT_TEXT = "没有命中：资料里没有与问题相关的内容"
export const KS_NO_HIT_HINT = "换个问法，或勾选其它模块再试"
export const KS_UNAVAILABLE_TEXT = "检索不可用"
export const KS_TRANSPORT_ERROR = "检索请求失败，请稍后重试"

export const KS_INDEX_HINT = "只索引 .md / .txt 文件；首次提问会建立索引，可能较慢"
export const KS_MANAGE_HINT = "仅超级管理员可以维护模块与路径"
export const KS_SELECT_HINT = "勾选左侧模块后才能提问"
export const KS_QUESTION_PLACEHOLDER = "输入问题，例如：指示灯红色常亮代表什么？"

export const KS_MODULE_DIALOG_TITLE = "知识库模块"
export const KS_DELETE_MESSAGE = "删除后该模块不再参与检索；资料目录与索引文件不会被删除。"
export const KS_INDEX_DONE = "索引已更新"
export const KS_INDEX_FAILED = "索引失败"

/** 提问返回条数：v1 用后端配置默认，不在 UI 调节。 */
export const KS_TOP_K_DEFAULT = 4

// ── 自动评测 ──

export const KS_RIGHT_TABS = [
  { key: "query", label: "提问" },
  { key: "eval", label: "自动评测" },
]
export const KS_EVAL_TITLE = "自动评测"
export const KS_EVAL_SYNTHETIC_LABEL = "合成评测集，结果偏乐观"
export const KS_EVAL_TRIGGER = "发起评测"
export const KS_EVAL_EMPTY = "暂无评测记录"
export const KS_EVAL_EMPTY_HINT = "超管可发起一次合成评测，产出 Recall@k / MRR / 误命中率"
export const KS_EVAL_RUNNING = "评测进行中"
export const KS_EVAL_FAILED = "评测失败"
export const KS_EVAL_DONE = "已完成"
export const KS_EVAL_PENDING = "排队中"
export const KS_EVAL_POS_DEFAULT = 30
export const KS_EVAL_NEG_DEFAULT = 10
export const KS_EVAL_TOTAL_MAX = 100
export const KS_EVAL_ESTIMATE_NOTE = "启发式预估，不含首次建索引；实际以账本为准"
export const KS_EVAL_POLL_MS = 2000
export const KS_EVAL_DIALOG_TITLE = "发起自动评测"
export const KS_EVAL_NO_CHAT_MODEL = "没有可用的 chat 类模型配置，请先在运营后台登记"
