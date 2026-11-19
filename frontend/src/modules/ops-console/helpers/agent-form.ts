/**
 * Agent 配置抽屉的草稿与接口入参互转。
 *
 * 业务：
 * 1. 草稿形状：类型在 UI 是单选（`kind`），接口字段是数组（`kinds`）
 * 2. draftFromAgent / emptyDraft: 编辑预填与新建初值
 * 3. draftToInput: 提交前打包，空类型提交成空数组
 * 4. draftProblem: 提交前校验，返回第一条中文提示（空串表示通过）
 */
import type { OpsAgent, OpsAgentInput, OpsAgentKind } from "../types"

/** 抽屉表单草稿：一份配置只有一个类型，故用单值 */
export interface AgentFormDraft {
  name: string
  model_config_id: number | null
  system_prompt: string
  kind: OpsAgentKind | ""
}

/** 新建时的空草稿：类型留空，由用户选 */
export function emptyDraft(): AgentFormDraft {
  return { name: "", model_config_id: null, system_prompt: "", kind: "" }
}

/** 编辑预填：后端 `kinds` 取第一项（1:1 口径），未分类即为空 */
export function draftFromAgent(agent: OpsAgent): AgentFormDraft {
  return {
    name: agent.name || "",
    model_config_id: agent.model_config_id,
    system_prompt: agent.system_prompt || "",
    kind: agent.kinds?.[0] ?? "",
  }
}

/** 草稿 → 接口入参。名称去首尾空白；未选类型提交空数组。 */
export function draftToInput(draft: AgentFormDraft): OpsAgentInput {
  return {
    name: draft.name.trim(),
    model_config_id: draft.model_config_id,
    system_prompt: draft.system_prompt,
    kinds: draft.kind ? [draft.kind] : [],
  }
}

/** 提交前校验：返回第一条不满足项的中文提示；全部满足返回空串。 */
export function draftProblem(input: OpsAgentInput): string {
  if (!input.name) return "请填写名称"
  if (input.model_config_id == null) return "请选择模型配置"
  if (!input.kinds.length) return "请选择类型"
  return ""
}
