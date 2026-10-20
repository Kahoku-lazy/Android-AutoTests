/** case-manager 项目化文档用例类型（wire snake_case） */

export type SystemType = "ANDROID" | "WEB" | "IOS" | "API"
export type CaseType = "FUNC" | "AUTO"
export type Priority = "P0" | "P1" | "P2"
export type BusinessType = "appliance" | "lighting" | "app"

/** 一条步骤：动作 + 断言；id 只在读接口回来时存在，保存时按位置整段替换 */
export interface CaseStep {
  id?: number
  action: string
  assertion: string
}

export interface CaseProject {
  id: number
  name: string
  description: string
  created_by: string
  created_at: string
  updated_at: string
  case_count: number
}

export interface TreeDirectoryNode {
  type: "directory"
  id: number
  name: string
  sort_order: number
  children: TreeNode[]
}

export interface TreeFileNode {
  type: "file"
  id: number
  name: string
  sort_order: number
  updated_at: string
}

export type TreeNode = TreeDirectoryNode | TreeFileNode

export interface ProjectTreePayload {
  project: CaseProject
  tree: TreeNode[]
}

export interface CaseFileMeta {
  id: number
  project_id: number
  directory_id: number | null
  name: string
  sort_order: number
  created_by: string
  created_at: string
  updated_at: string
  case_count: number
}

export interface CaseDefinition {
  id: string
  project_id: number
  file_id: number
  directory_id: number | null
  title: string
  priority: Priority
  system: SystemType
  case_type: CaseType
  business_type: BusinessType
  module: string
  precondition: string
  steps: CaseStep[]
  step_count: number
  sort_order: number
  created_by: string
  updated_by: string
  created_at: string
  updated_at: string
}

export interface CaseFileSheet {
  file: CaseFileMeta
  rows: CaseDefinition[]
}

export interface SheetRowDraft {
  /** 已保存行用真实 id；新建未保存用 temp-* */
  id: string
  title: string
  priority: Priority
  system: SystemType
  case_type: CaseType
  business_type: BusinessType
  module: string
  precondition: string
  steps: CaseStep[]
  updated_at: string
  dirty: boolean
  isNew: boolean
}

export interface EnumOption<T extends string = string> {
  value: T
  label: string
  /** 选项附注（如 IOS 暂不支持执行） */
  note?: string
}

export const PRIORITY_OPTIONS: EnumOption<Priority>[] = [
  { value: "P0", label: "P0 必测" },
  { value: "P1", label: "P1 应测" },
  { value: "P2", label: "P2 可测" },
]

export const SYSTEM_OPTIONS: EnumOption<SystemType>[] = [
  { value: "ANDROID", label: "ANDROID" },
  { value: "WEB", label: "WEB" },
  { value: "IOS", label: "IOS", note: "暂不支持执行" },
  { value: "API", label: "API" },
]

export const CASE_TYPE_OPTIONS: EnumOption<CaseType>[] = [
  { value: "FUNC", label: "功能" },
  { value: "AUTO", label: "自动化" },
]

export const BUSINESS_TYPE_OPTIONS: EnumOption<BusinessType>[] = [
  { value: "appliance", label: "家电" },
  { value: "lighting", label: "照明" },
  { value: "app", label: "APP" },
]

/** 单段动作 / 断言的字符上限，与后端 api_definitions.MAX_STEP_TEXT 同口径 */
export const MAX_STEP_TEXT = 2000
