import type { OpsAgent, OpsAgentInput, OpsAgentKind } from "../types"

export interface AgentFormDraft {
  name: string
  model_config_id: number | null
  system_prompt: string
  kind: OpsAgentKind | ""
}

export function emptyDraft(): AgentFormDraft {
  return { name: "", model_config_id: null, system_prompt: "", kind: "" }
}

export function draftFromAgent(agent: OpsAgent): AgentFormDraft {
  return {
    name: agent.name || "",
    model_config_id: agent.model_config_id,
    system_prompt: agent.system_prompt || "",
    kind: agent.kinds?.[0] ?? "",
  }
}

export function draftToInput(draft: AgentFormDraft): OpsAgentInput {
  return {
    name: draft.name.trim(),
    model_config_id: draft.model_config_id,
    system_prompt: draft.system_prompt,
    kinds: draft.kind ? [draft.kind] : [],
  }
}

export function draftProblem(input: OpsAgentInput): string {
  if (!input.name) return "请填写名称"
  if (input.model_config_id == null) return "请选择模型配置"
  if (!input.kinds.length) return "请选择类型"
  return ""
}
