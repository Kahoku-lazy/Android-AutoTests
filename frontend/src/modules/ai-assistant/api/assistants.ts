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

export async function deleteAssistant(assistantId: string): Promise<void> {
  await djangoClient.delete(`/ai/assistants/${assistantId}/`)
}

export async function updateAssistant(
  assistantId: string,
  payload: {
    display_name: string
    role_id: string
    tools: ToolSelection[]
    revision?: number
    avatar?: File | null
    clearAvatar?: boolean
  },
): Promise<AssistantCard> {
  const body = new FormData()
  body.set("display_name", payload.display_name)
  body.set("role_id", payload.role_id)
  body.set("tools", JSON.stringify(payload.tools))
  if (payload.revision !== undefined) body.set("revision", String(payload.revision))
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

export interface EvalScoreItem {
  metric_key: string
  score: number
  threshold: number
  reason: string
}

export interface EvalScoreMissing {
  metric_key: string
  reason: string
}

export interface EvalScore {
  id: number
  target_kind: string
  target_id: string
  prompt_fingerprint: string
  source_ref: string
  judge_model: string
  created_at: string
  items: EvalScoreItem[]
  missing?: EvalScoreMissing[]
}

export interface EvalCandidate {
  source_ref: string
  dir: string
  file: string
  task: string
  handover: string
  handover_chars: number
  phase: string
  cost_s: number | null
  modified_at: string
}

export async function runEval(
  kind: "assistant" | "workflow",
  targetId: string,
  sourceRef = "",
): Promise<EvalScore> {
  const { data } = await djangoClient.post<DjangoResponse<{ score: EvalScore }>>(
    "/ai/eval-scores/",
    { kind, target_id: targetId, source_ref: sourceRef },
  )
  if (!data.data) throw data
  return data.data.score
}

export async function fetchEvalScores(
  kind: "assistant" | "workflow",
  targetId: string,
  limit = 20,
): Promise<EvalScore[]> {
  const { data } = await djangoClient.get<DjangoResponse<{ scores: EvalScore[] }>>(
    "/ai/eval-scores/",
    { params: { kind, target_id: targetId, limit } },
  )
  return data.data?.scores || []
}

export interface EvalMethod {
  key: string
  name: string
  target: string
  description: string
  criteria: string
  threshold: number
}

export interface EvalCaseStep {
  id?: number
  sort_order?: number
  action: string
  assertion: string
  anchor: Record<string, string>
}

export interface EvalCase {
  id: number
  title: string
  note: string
  enabled: boolean
  step_count?: number
  steps: EvalCaseStep[]
}

export interface EvalSuiteRun {
  id: number
  target_id: string
  created_at: string
  judge_model: string
  method_key: string
  report_html: string
  items: { metric_key: string; score: number; reason: string }[]
  cases: {
    case_id: string
    case_title: string
    steps_total: number
    steps_passed: number
    cost_s: number
    score: number | null
    reason: string
  }[]
}

export async function fetchEvalMethods(): Promise<EvalMethod[]> {
  const { data } =
    await djangoClient.get<DjangoResponse<{ methods: EvalMethod[] }>>("/ai/eval-methods/")
  return data.data?.methods || []
}

export async function fetchEvalCases(): Promise<EvalCase[]> {
  const { data } = await djangoClient.get<DjangoResponse<{ cases: EvalCase[] }>>("/ai/eval-cases/")
  return data.data?.cases || []
}

export async function createEvalCase(payload: {
  title: string
  note?: string
  steps: EvalCaseStep[]
}): Promise<EvalCase> {
  const { data } = await djangoClient.post<DjangoResponse<{ case: EvalCase }>>(
    "/ai/eval-cases/",
    payload,
  )
  if (!data.data) throw data
  return data.data.case
}

export async function updateEvalCase(
  caseId: number,
  payload: { title?: string; note?: string; enabled?: boolean; steps?: EvalCaseStep[] },
): Promise<EvalCase> {
  const { data } = await djangoClient.patch<DjangoResponse<{ case: EvalCase }>>(
    `/ai/eval-cases/${caseId}/`,
    payload,
  )
  if (!data.data) throw data
  return data.data.case
}

export async function deleteEvalCase(caseId: number): Promise<void> {
  await djangoClient.delete(`/ai/eval-cases/${caseId}/`)
}

export async function runSuiteEval(payload: {
  target_kind: "assistant" | "workflow"
  target_id: string
  case_ids: string[]
  serial: string
}): Promise<EvalSuiteRun> {
  const { data } = await djangoClient.post<DjangoResponse<{ score: EvalSuiteRun }>>(
    "/ai/eval-runs/",
    payload,
  )
  if (!data.data) throw data
  return data.data.score
}

export async function fetchSuiteRuns(targetId = ""): Promise<EvalSuiteRun[]> {
  const { data } = await djangoClient.get<DjangoResponse<{ scores: EvalSuiteRun[] }>>(
    "/ai/eval-runs/",
    { params: { target_id: targetId } },
  )
  return data.data?.scores || []
}

export async function fetchEvalReport(runId: number): Promise<string> {
  const { data } = await djangoClient.get<string>(`/ai/eval-reports/${runId}/`, {
    responseType: "text",
    transformResponse: [(body) => body],
  })
  return data
}

export async function publishAssistant(assistantId: string): Promise<{ version: number }> {
  const { data } = await djangoClient.post<DjangoResponse<{ version: number }>>(
    `/ai/assistants/${assistantId}/publish/`,
  )
  if (!data.data) throw data
  return data.data
}

export async function publishWorkflow(workflowId: number): Promise<{ version: number }> {
  const { data } = await djangoClient.post<DjangoResponse<{ version: number }>>(
    `/ai/sop-workflows/${workflowId}/publish/`,
  )
  if (!data.data) throw data
  return data.data
}

export async function fetchEvalCandidates(
  kind: "assistant" | "workflow",
  targetId: string,
): Promise<EvalCandidate[]> {
  const { data } = await djangoClient.get<DjangoResponse<{ candidates: EvalCandidate[] }>>(
    "/ai/eval-candidates/",
    { params: { kind, target_id: targetId } },
  )
  return data.data?.candidates || []
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

export async function deleteThread(threadId: string): Promise<void> {
  await djangoClient.post(`/ai/assistants/threads/${threadId}/delete/`)
}
