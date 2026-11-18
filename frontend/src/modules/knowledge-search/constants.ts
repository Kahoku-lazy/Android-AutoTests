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
