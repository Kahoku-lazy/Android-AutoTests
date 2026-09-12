/** case-manager 项目化文档用例类型（wire snake_case） */

export type TestType = 'app' | 'web' | 'api' | 'func'
export type BusinessType = 'appliance' | 'lighting' | 'app'

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
  type: 'directory'
  id: number
  name: string
  sort_order: number
  children: TreeNode[]
}

export interface TreeFileNode {
  type: 'file'
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
  test_type: TestType
  business_type: BusinessType
  module: string
  precondition: string
  steps: string
  expected_result: string
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
  test_type: TestType
  business_type: BusinessType
  module: string
  precondition: string
  steps: string
  expected_result: string
  updated_at: string
  dirty: boolean
  isNew: boolean
}

export const TEST_TYPE_OPTIONS = [
  { value: 'app' as const, label: 'APP' },
  { value: 'web' as const, label: 'WEB' },
  { value: 'api' as const, label: 'API' },
  { value: 'func' as const, label: 'FUNC' },
]

export const BUSINESS_TYPE_OPTIONS = [
  { value: 'appliance' as const, label: '家电' },
  { value: 'lighting' as const, label: '照明' },
  { value: 'app' as const, label: 'APP' },
]
