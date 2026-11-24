export const KS_PAGE_TITLE = "知识库"
export const KS_PAGE_ICON = "book-open"

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

export const KS_TOP_K_DEFAULT = 4

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

export const KS_EVAL_PHASE_TEXT: Record<string, string> = {
  indexing: "正在建立索引…",
  generating: "模型正在出题…",
  retrieving: "逐题检索中",
}

export const KS_EVAL_EXPLAINER = [
  {
    title: "评测集怎么来",
    body: "从模块资料目录采样切块（与索引同参数），由所选 chat 模型按块出题，该块来源文档即正确答案（gold）；另生成与语料无关的负样本。题目、gold 与来源片段随运行落库，可逐题审计。",
  },
  {
    title: "检索怎么跑",
    body: "每题走与「提问」完全相同的检索桥：top_k=5，相似度阈值取库配置，命中按相似度降序。正题看 gold 文档排第几，负样本看是否竟然有命中。",
  },
  {
    title: "指标怎么算",
    body: "rank = gold 文档在命中列表的首个位置。Recall@k = rank≤k 的正题占比；MRR = 1/rank 的均值（未命中记 0）；误命中率 = 负样本有命中的比例。",
  },
  {
    title: "怎么读结果",
    body: "合成题与原文词汇相近，结果偏乐观：适合纵向对比（改阈值/切块后重跑同一模块），不宜当绝对达标线。接回 Agent 前需人工金标复核（规划中）。",
  },
]
