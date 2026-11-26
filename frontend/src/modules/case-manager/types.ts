export type LibraryKind = "automation" | "functional"
export type SystemType = "ANDROID" | "WEB" | "IOS" | "API"
export type Priority = "P0" | "P1" | "P2"
export type BusinessType = "appliance" | "lighting" | "app"

export interface StepAnchorHint {
  page?: string
  entry?: string
  target?: string
}

export interface StepLogHint {
  sku?: string
  port?: number
  keywords?: string[]
}

export interface CaseStep {
  id?: number
  action: string
  assertion: string
  anchor?: StepAnchorHint
  log?: StepLogHint
}

export interface CaseProject {
  id: number
  name: string
  description: string
  library_kind: LibraryKind
  created_by: string
  created_at: string
  updated_at: string
  case_count: number
  case_limit: number
}

export interface CaseRow {
  id: string
  project_id: number
  title: string
  priority: Priority
  system: SystemType
  business_type: BusinessType
  module: string
  precondition: string
  steps: CaseStep[]
  step_count: number
  sort_order: number
  updated_at: string
}

export interface SheetView {
  hidden_columns: string[]
  filters: Record<string, string>
  sort: { field: string; direction: "asc" | "desc" }
  group_by: string
}

export interface ProjectSheet {
  project: Pick<CaseProject, "id" | "name" | "library_kind" | "case_count" | "case_limit">
  rows: CaseRow[]
  view: SheetView
}

export const LIBRARY_OPTIONS: { value: LibraryKind; label: string }[] = [
  { value: "automation", label: "自动化" },
  { value: "functional", label: "功能" },
]

export const PRIORITY_OPTIONS = [
  { value: "P0", label: "P0" },
  { value: "P1", label: "P1" },
  { value: "P2", label: "P2" },
]

export const SYSTEM_OPTIONS = [
  { value: "ANDROID", label: "ANDROID" },
  { value: "WEB", label: "WEB" },
  { value: "IOS", label: "IOS" },
  { value: "API", label: "API" },
]

export const BUSINESS_OPTIONS = [
  { value: "appliance", label: "家电" },
  { value: "lighting", label: "照明" },
  { value: "app", label: "APP" },
]

export const SHEET_COLUMNS = [
  { key: "id", label: "编号" },
  { key: "priority", label: "优先级" },
  { key: "system", label: "系统" },
  { key: "business_type", label: "业务" },
  { key: "module", label: "模块" },
  { key: "title", label: "标题" },
  { key: "steps", label: "步骤" },
  { key: "updated_at", label: "更新时间" },
]

export const GROUP_OPTIONS = [
  { key: "", label: "不分组" },
  { key: "module", label: "按模块" },
  { key: "priority", label: "按优先级" },
]

export const DEFAULT_SHEET_VIEW: SheetView = {
  hidden_columns: [],
  filters: {},
  sort: { field: "sort_order", direction: "asc" },
  group_by: "",
}
