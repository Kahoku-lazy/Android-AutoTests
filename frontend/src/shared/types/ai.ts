export type AgentStatus = "active" | "paused" | "error"

export interface AgentRecord {
  id: number
  name: string
  status: AgentStatus

  task_kind?: string
  model_name?: string
  model_provider?: string
  strong_model_name?: string
  strong_enabled?: boolean
  available_models?: string[]
  tags?: string[]
  description?: string
  avatar_url?: string
  avatar?: string
  tool_count?: number
  route_configs?: RouteConfigMap
}

export interface RouteModelConfig {
  provider?: string
  model_name?: string
  api_key?: string
  base_url?: string
}

export interface RouteConfig {
  name?: string
  avatar?: string
  planner?: RouteModelConfig
  executor?: RouteModelConfig
  verifier?: RouteModelConfig
}

export interface RouteConfigMap {
  device_control?: RouteConfig
  case_authoring?: RouteConfig
}

export type AgentRoute = "device_control"

export interface TaskRecord {
  id: number
  title: string
  task_kind?: string
  goal: string
  status: string
  result?: string
  device_serial?: string

  device_label?: string

  case_title?: string

  case_label?: string

  case_rows?: { project: string; id: string; title: string }[]

  assistant_name?: string

  attachment_filename?: string

  attachment_names?: string[]
  created_at?: string
  started_at?: string
  finished_at?: string
  deepseek_cost?: number

  report_run?: string

  report_name?: string
  workflow_id?: number | null
  workflow_name?: string
  orchestration?: string
  kind?: string
}

export interface TaskSubmitPayload {
  title: string
  agent_id: number
  device_serial: string
  case_title?: string
}

export interface WorkflowFilterOption {
  id: number
  name: string
}

export interface TaskListResponse {
  status?: boolean
  data?: { tasks: TaskRecord[]; workflows?: WorkflowFilterOption[] }
  message?: string
}

export interface TaskStats {
  total: number
  running: number
  pending: number
  success: number
  failed: number
  interrupted: number
  cancelled: number
  finished: number
  success_rate: number

  agents?: TaskAgentStats[]
}

export interface TaskAgentStats extends Omit<TaskStats, "agents"> {
  id: number
  name: string
}

export interface TaskStatsResponse {
  status?: boolean
  data?: TaskStats
  message?: string
}

export interface TaskFailedItem {
  item?: string
  reason?: string
  action?: string
  assert?: string
  actual?: string
}

export interface TaskRunStep {
  action: string
  assert: string
}

export interface TaskRunExecutorOut {
  result?: string

  click_timer?: string

  screenshot?: string

  action?: string

  message?: string
}

export interface TaskRunVerifierOut {
  result?: boolean | string

  click_timer?: string

  logAssertionTimer?: string

  logAssertionInfo?: string

  screenshot?: string

  actual?: string

  action?: string

  assert?: string
  summary?: string
  completed?: string[]
  failed?: TaskFailedItem[]
}

export interface TaskLogFeature {
  id?: number
  module?: string
  feature?: string
}

export interface TaskLogOccurrence {
  timestamp?: string
  source?: string
  text?: string
  grade?: string
}

export interface TaskLogLine {
  timestamp?: string
  source?: string
  text?: string
  port?: number
}

export interface TaskLogEvidenceHit {
  keyword?: string

  grade?: string
  count?: number
  timestamps?: string[]
  occurrences?: TaskLogOccurrence[]
  features?: TaskLogFeature[]
  baseline_occurrences?: Array<{ timestamp?: string; text?: string }>
}

export interface TaskLogEvidence {
  channel?: string
  window_id?: string
  window_opened_at?: string
  action_time?: string
  action_times?: string[]
  threshold_seconds?: number
  baseline_seconds?: number
  window_line_count?: number

  conclusion?: string
  hits?: TaskLogEvidenceHit[]
  before_action?: Array<{ keyword?: string; timestamp?: string; text?: string; grade?: string }>
  out_of_window?: Array<{
    keyword?: string
    timestamp?: string
    text?: string
    grade?: string
    delta_seconds?: number
  }>

  lines?: TaskLogLine[]
}

export interface TaskLogCheckClick {
  action_time?: string
  screenshot_path?: string
}

export interface TaskLogCheck {
  clicks?: TaskLogCheckClick[]

  log?: TaskLogEvidence | null
}

export interface TaskRunLogEntry {
  action?: string
  assert?: string
  loop: number
  executor?: string | TaskRunExecutorOut
  verifier?: TaskRunVerifierOut

  screenshot?: string

  log_evidence?: TaskLogEvidence

  executor_log_check?: TaskLogCheck

  goal?: string
  steps?: Array<string | TaskRunStep>
  verification?: string
  result?: string
}

export interface TaskRunPlan {
  goal?: string
  steps?: Array<string | TaskRunStep>

  verification?: string
}

export interface TaskRunPayload {
  status?: string
  summary?: string
  reason?: string
  message?: string
  completed?: string[]
  failed?: TaskFailedItem[]
  plans?: TaskRunPlan[]
  log?: TaskRunLogEntry[]
  usage?: Record<string, unknown>
  models?: { planner?: string; executor?: string; verifier?: string; max_loops?: number }
  max_loops?: number
}

export interface TaskDetail {
  id: number
  title: string
  task_kind?: string
  goal: string
  status: string
  device_serial?: string
  device_label?: string
  assistant_name?: string
  attachment_filename?: string

  attachment?: string

  planner_input?: string

  load_message?: string

  yaml_body?: string

  documents?: { filename: string; body: string }[]
  created_at?: string
  started_at?: string
  finished_at?: string
  input_tokens?: number
  output_tokens?: number
  cache_input_tokens?: number
  model_usage?: Record<
    string,
    { input_tokens?: number; output_tokens?: number; cache_input_tokens?: number }
  >
  deepseek_cost?: number
  run?: TaskRunPayload
}

export interface TaskDetailResponse {
  status?: boolean
  data?: TaskDetail
  message?: string
}

export interface TaskReportBlock {
  phase?: string

  title?: string
  items?: TaskReportBlockItem[]
}

export interface TaskReportBlockItem {
  seq: number
  event_type?: string
  label?: string
  detail?: string
  time?: string

  count?: number
  step_seq?: number | null
  attempt?: number | null
  role_name?: string
  role_kind?: string
  model?: string
  status?: string

  media_id?: number | null
  handover?: string
  verdict?: TaskReportRoundVerdict | null
}

export interface TaskReportRoundVerdict {
  passed?: boolean | null
  message?: string
}

export interface TaskReportRound {
  round_id: number

  role?: string
  role_name?: string

  role_kind?: string
  model?: string
  step_seq?: number | null

  attempt?: number | null

  subject?: string
  duty?: string
  handover?: string
  verdict?: TaskReportRoundVerdict | null
  blocks?: TaskReportBlock[]

  model_ms?: number

  running?: boolean
}

export interface TaskReportStep {
  seq: number
  action?: string
  expected?: string

  outcome?: string

  duration_ms?: number

  model_ms?: number

  tool_ms?: number

  idle_ms?: number

  interrupt?: string

  interrupt_kind?: string

  interrupt_tool?: string

  running?: boolean
}

export interface TaskReportCase {
  title?: string
  outcome?: string
  steps?: TaskReportStep[]
  round_ids?: number[]

  duration_ms?: number

  running?: boolean
}

export interface TaskReportTask {
  id?: number
  title?: string
  status?: string
  task_kind?: string
  assistant?: string
  device?: string
  case_title?: string
  started_at?: string
  finished_at?: string
  cost_total?: number
  result?: string
}

export interface TaskReportConclusion {
  outcome?: string
  delivery?: string
  verdicts?: Array<{
    passed?: boolean
    message?: string
    role_name?: string
    step_seq?: number | null
    attempt?: number | null
  }>
}

export interface TaskReportEvent {
  seq?: number
  time?: string
  role_kind?: string
  role_name?: string
  event_type?: string
  label?: string
  detail?: string
  model?: string
  status?: string
  count?: number
}

export interface TaskArtifactSummary {
  counts?: {
    states?: number
    transitions?: number
    scenarios?: number
    cases?: number
  }
  diagram?: string
}

export interface TaskFactsSummary {
  blocking?: number
  warnings?: number
}

export interface TaskReportPayload {
  task?: TaskReportTask
  rounds?: TaskReportRound[]
  cases?: TaskReportCase[]
  conclusion?: TaskReportConclusion | null

  events?: TaskReportEvent[]

  case_import?: Record<string, unknown> | null

  artifact?: TaskArtifactSummary | null

  facts?: TaskFactsSummary | null
}

export interface TaskReportResponse {
  status?: boolean
  message?: string
  data?: TaskReportPayload
}

export interface TaskDeleteResponse {
  status?: boolean
  message?: string
}

export interface TaskSubmitResponse {
  status?: boolean
  data?: { id?: number; status?: string; result?: string }
  message?: string
}

export interface AgentListResponse {
  status?: boolean
  data?: { agents: AgentRecord[] }
  message?: string
}

export interface AgentDetailResponse {
  status?: boolean
  data?: { agent: AgentRecord }
  message?: string
}

export interface AgentOpResponse {
  status?: boolean
  data?: { id?: number }
  message?: string
}
