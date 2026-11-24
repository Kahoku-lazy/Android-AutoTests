/** 助手名片与测试对话。任务清单仍走 api/agents.ts，不经过这里。 */
import djangoClient from "@/shared/api-client"
import type { DjangoResponse } from "@/shared/api-client"
import type {
  AssistantCard,
  SopWorkflow,
  AssistantThread,
  RoleOption,
  ThreadLog,
  ThreadMessage,
  ToolCatalogDomain,
  ToolSelection,
} from "../types"

export async function listAssistants(): Promise<AssistantCard[]> {
  const { data } = await djangoClient.get<DjangoResponse<AssistantCard[]>>("/ai/assistants/")
  return data.data || []
}

export async function listRoleOptions(): Promise<RoleOption[]> {
  const { data } = await djangoClient.get<DjangoResponse<RoleOption[]>>("/ai/roles/")
  return data.data || []
}

export async function listToolCatalog(): Promise<ToolCatalogDomain[]> {
  const { data } = await djangoClient.get<DjangoResponse<ToolCatalogDomain[]>>("/ai/tool-catalog/")
  return data.data || []
}

export async function createAssistant(payload: {
  display_name: string
  role_id: string
  tools: ToolSelection[]
  avatar?: File | null
}): Promise<AssistantCard> {
  const body = new FormData()
  body.set("display_name", payload.display_name)
  body.set("role_id", payload.role_id)
  body.set("tools", JSON.stringify(payload.tools))
  if (payload.avatar) body.set("avatar", payload.avatar)
  const { data } = await djangoClient.post<DjangoResponse<AssistantCard>>("/ai/assistants/", body, {
    headers: { "Content-Type": "multipart/form-data" },
  })
  if (!data.data) throw data
  return data.data
}

/** 删除助手名片。只删名片本身，对话记录、历史任务与 Agent 配置都保留。 */
export async function deleteAssistant(assistantId: string): Promise<void> {
  await djangoClient.delete(`/ai/assistants/${assistantId}/`)
}

/** 编辑名片：PATCH 同一张卡片；头像三态由 clearAvatar / avatar 决定。 */
export async function updateAssistant(
  assistantId: string,
  payload: {
    display_name: string
    role_id: string
    tools: ToolSelection[]
    avatar?: File | null
    clearAvatar?: boolean
  },
): Promise<AssistantCard> {
  const body = new FormData()
  body.set("display_name", payload.display_name)
  body.set("role_id", payload.role_id)
  body.set("tools", JSON.stringify(payload.tools))
  if (payload.avatar) body.set("avatar", payload.avatar)
  if (payload.clearAvatar) body.set("clear_avatar", "1")
  const { data } = await djangoClient.patch<DjangoResponse<AssistantCard>>(
    `/ai/assistants/${assistantId}/`,
    body,
    { headers: { "Content-Type": "multipart/form-data" } },
  )
  if (!data.data) throw data
  return data.data
}

export async function avatarUrl(assistantId: string): Promise<string> {
  const { data } = await djangoClient.get<DjangoResponse<{ avatar: string }>>(
    `/ai/assistants/${assistantId}/avatar/`,
  )
  const raw = data.data?.avatar || ""
  return raw ? `data:image/jpeg;base64,${raw}` : ""
}

export interface EvalFailure {
  sample: string
  ruler: string
  text: string
}

export interface EvalStep {
  role: string
  text: string
  tool: string
  input: Record<string, unknown>
}

export interface EvalSample {
  sample: string
  title: string
  passed: boolean
  failures: EvalFailure[]
  steps: EvalStep[]
}

export interface EvalRunDetail {
  id: number
  status: string
  phase: string
  progress_done: number
  progress_total: number
  error: string
  samples: EvalSample[]
}

export async function runEval(
  kind: "assistant" | "workflow",
  targetId: string,
): Promise<{ id: number }> {
  const { data } = await djangoClient.post<DjangoResponse<{ id: number }>>("/ai/evals/run/", {
    kind,
    target_id: targetId,
  })
  return data.data || { id: 0 }
}

export async function fetchEvalRun(id: number): Promise<EvalRunDetail> {
  const { data } = await djangoClient.get<DjangoResponse<EvalRunDetail>>(`/ai/evals/runs/${id}/`)
  if (!data.data) throw data
  return data.data
}

export async function listSopWorkflows(): Promise<SopWorkflow[]> {
  const { data } = await djangoClient.get<DjangoResponse<SopWorkflow[]>>("/ai/sop-workflows/")
  return data.data || []
}

export async function createSopWorkflow(payload: {
  name: string
  orchestration: string
  kind: string
  executor_assistant_id?: string
  verifier_assistant_id?: string
  leader_assistant_id?: string
  members?: { assistant_id: string; description: string }[]
}): Promise<SopWorkflow> {
  const { data } = await djangoClient.post<DjangoResponse<SopWorkflow>>(
    "/ai/sop-workflows/",
    payload,
  )
  if (!data.data) throw data
  return data.data
}

/** 编辑工作流：三字段整幅回写，编号与创建时间不变。 */
export async function updateSopWorkflow(
  workflowId: number,
  payload: {
    name: string
    executor_assistant_id?: string
    verifier_assistant_id?: string
    leader_assistant_id?: string
    members?: { assistant_id: string; description: string }[]
  },
): Promise<SopWorkflow> {
  const { data } = await djangoClient.patch<DjangoResponse<SopWorkflow>>(
    `/ai/sop-workflows/${workflowId}/`,
    payload,
  )
  if (!data.data) throw data
  return data.data
}

/** 删除工作流：只删记录，助手名片与历史任务不受影响。 */
export async function deleteSopWorkflow(workflowId: number): Promise<void> {
  await djangoClient.delete(`/ai/sop-workflows/${workflowId}/`)
}

export async function listAutomationProjects(): Promise<
  { id: number; name: string; rows: { id: string; title: string }[] }[]
> {
  const { data } = await djangoClient.get<
    DjangoResponse<{ id: number; name: string; rows: { id: string; title: string }[] }[]>
  >("/cases/projects/automation/")
  return data.data || []
}

export async function runSopWorkflow(payload: {
  workflowId: number
  title: string
  yaml?: File | null
  caseIds?: string[]
  serial?: string
  material?: File | null
}): Promise<{ id: number; status: string }> {
  const body = new FormData()
  body.set("title", payload.title)
  body.set("workflow_id", String(payload.workflowId))
  body.set("case_source", payload.caseIds?.length ? "platform" : "yaml")
  if (payload.yaml) body.set("config", payload.yaml)
  if (payload.caseIds?.length) body.set("case_ids", JSON.stringify(payload.caseIds))
  if (payload.serial) body.set("device_serial", payload.serial)
  if (payload.material) body.set("material", payload.material)
  const { data } = await djangoClient.post<DjangoResponse<{ id: number; status: string }>>(
    "/tasks/submit/",
    body,
    { headers: { "Content-Type": "multipart/form-data" } },
  )
  if (!data.data) throw data
  return data.data
}

export async function listThreads(assistantId: string): Promise<AssistantThread[]> {
  const { data } = await djangoClient.get<DjangoResponse<AssistantThread[]>>(
    `/ai/assistants/${assistantId}/threads/`,
  )
  return data.data || []
}

export async function createThread(assistantId: string): Promise<AssistantThread> {
  const { data } = await djangoClient.post<DjangoResponse<AssistantThread>>(
    `/ai/assistants/${assistantId}/threads/`,
  )
  if (!data.data) throw data
  return data.data
}

export async function listThreadLogs(threadId: string): Promise<ThreadLog[]> {
  const { data } = await djangoClient.get<DjangoResponse<ThreadLog[]>>(
    `/ai/assistants/threads/${threadId}/logs/`,
  )
  return data.data || []
}

export async function issueLogTicket(threadId: string, reportId: string): Promise<string> {
  const { data } = await djangoClient.post<DjangoResponse<{ ticket: string }>>(
    `/ai/assistants/threads/${threadId}/logs/${reportId}/`,
  )
  if (!data.data?.ticket) throw data
  return data.data.ticket
}

export function threadLogUrl(threadId: string, reportId: string, ticket = ""): string {
  const base = `/api/ai/assistants/threads/${threadId}/logs/${reportId}/`
  return ticket ? `${base}?ticket=${encodeURIComponent(ticket)}` : base
}

export async function pollThread(
  threadId: string,
): Promise<{ status: string; messages: ThreadMessage[] }> {
  const { data } = await djangoClient.get<
    DjangoResponse<{ status: string; messages: ThreadMessage[] }>
  >(`/ai/assistants/threads/${threadId}/`)
  return data.data || { status: "idle", messages: [] }
}

export async function sendThread(threadId: string, content: string): Promise<void> {
  await djangoClient.post(`/ai/assistants/threads/${threadId}/`, { content })
}

export async function cancelThread(threadId: string): Promise<void> {
  await djangoClient.delete(`/ai/assistants/threads/${threadId}/`)
}

/** 重命名对话栏；空标题表示回到前端默认的「对话 N」。 */
export async function renameThread(
  threadId: string,
  title: string,
): Promise<{ thread_id: string; title: string }> {
  const { data } = await djangoClient.patch<DjangoResponse<{ thread_id: string; title: string }>>(
    `/ai/assistants/threads/${threadId}/`,
    { title },
  )
  if (!data.data) throw data
  return data.data
}

/** 删除对话栏及其消息（不是取消）。 */
export async function deleteThread(threadId: string): Promise<void> {
  await djangoClient.post(`/ai/assistants/threads/${threadId}/delete/`)
}
