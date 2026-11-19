/** AI 助手模块常量。

智能体看板与对话工作流已下线；这里只留仍被任务清单发布弹窗引用的任务类型。
*/

/** 任务类型（AIAgent.task_kind / Task.task_kind） */
export const TASK_KIND_DEVICE_CONTROL = "device_control"
export const TASK_KIND_CASE_AUTHORING = "case_authoring"

export const EVAL_PASSED = "规则通过"
export const EVAL_FAILED = "未通过"
export const EVAL_UNAVAILABLE = "该组合还没有可观察的运行过程，不能评测"
export const EVAL_POLL_MS = 2000
