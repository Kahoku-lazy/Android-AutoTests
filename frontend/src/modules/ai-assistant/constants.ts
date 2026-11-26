export const TASK_KIND_DEVICE_CONTROL = "device_control"
export const TASK_KIND_CASE_AUTHORING = "case_authoring"

export const EVAL_METRIC_LABELS: Record<string, string> = {
  prompt_quality: "提示词质量",
  handover_quality: "交接文本质量",
}

export const EVAL_CRUMBS = [{ label: "平台助手", to: "/ai-assistant" }, { label: "评测" }]

export const EVAL_CASE_COLUMNS = [
  { dataIndex: "pick", title: "选", width: 56 },
  { dataIndex: "title", title: "题目", minWidth: 260 },
  { dataIndex: "stepCount", title: "步数", width: 88 },
]

export const EVAL_SUITE_COLUMNS = [
  { dataIndex: "title", title: "题目", minWidth: 240 },
  { dataIndex: "passed", title: "步骤通过", width: 108 },
  { dataIndex: "cost", title: "耗时", width: 88 },
  { dataIndex: "verdict", title: "判定", width: 104 },
]

export const EVAL_HISTORY_COLUMNS = [
  { dataIndex: "at", title: "时间", width: 150 },
  { dataIndex: "metrics", title: "指标与分数", minWidth: 240 },
  { dataIndex: "fingerprint", title: "提示词指纹", width: 190 },
]
