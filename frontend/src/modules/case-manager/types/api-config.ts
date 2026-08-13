/** API 测试用例 config_json TypeScript 类型定义。
 *
 * 与后端 apps/case_manager/schema_config.py 的 JSON Schema 完全对齐。
 * 新增/修改字段时需同步更新两边的定义。
 */

// ─── 用例信息 ───

export interface CaseInfo {
  /** 用例唯一标识，格式 API-YYYYMMDD-HHMMSS-XXXX */
  id: string
  /** 测试标题，必填 */
  title: string
  /** 测试点描述 */
  description: string
  /** 前置条件 */
  precondition: string
}

// ─── 变量提取规则 ───

export interface ExtractRule {
  /** 变量名（对应 {{name}}） */
  name: string
  /** JSONPath 表达式，如 $.data.token */
  path: string
}

// ─── 测试步骤 ───

export interface ApiStep {
  /** 步骤名称（用于列表显示） */
  name: string
  /** 接口域名 */
  domain: string
  /** 接口路径，支持 {{var}} */
  url: string
  /** HTTP 方法 */
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH' | 'HEAD' | 'OPTIONS'
  /** 请求头，支持 {{var}} */
  headers: Record<string, string>
  /** 请求体，支持 {{var}} */
  body: Record<string, unknown>
  /** 请求体 JSON Schema（用于数据校验） */
  request_schema: Record<string, unknown> | null
  /** 响应体 JSON Schema（用于断言，当 assert=true 时生效） */
  response_schema: Record<string, unknown> | null
  /** 变量提取规则 */
  extract: ExtractRule[]
  /** 是否对该步骤执行响应断言 */
  assert: boolean
}

// ─── 测试数据行 ───

export interface OutputSchema {
  /** 目标步骤下标 */
  step_index: number
  /** JSON Schema 校验规则 */
  schema: Record<string, unknown>
}

export interface TestDataRow {
  /** 输入变量，key 对应步骤中的 {{key}} */
  input: Record<string, string>
  /** 行级输出断言（可选） */
  output_schema: OutputSchema | null
}

// ─── 数据校验规则 ───

export interface ValidationRule {
  /** 校验哪个步骤的请求体 */
  step_index: number
  /** 是否启用该校验 */
  enabled: boolean
  /** JSON Schema 校验规则 */
  schema: Record<string, unknown> | null
}

// ─── 顶层配置 ───

export interface ApiConfigJson {
  /** 用例基本信息 */
  case_info: CaseInfo
  /** 测试步骤列表 */
  steps: ApiStep[]
  /** 测试数据 */
  test_data: TestDataRow[]
  /** 数据校验规则 */
  validation: ValidationRule[]
}

// ─── 变量引用解析（前端用） ───

/** 已解析的变量引用 */
export interface ResolvedVariable {
  /** 变量名（不含 {{}}） */
  name: string
  /** 匹配到的上游 extract（null = 未匹配，需警告） */
  resolved: {
    stepIndex: number
    stepName: string
    name: string
    path: string
  } | null
}

// ─── 默认值工厂 ───

export function defaultApiConfigJson(caseId = '', title = ''): ApiConfigJson {
  return {
    case_info: {
      id: caseId,
      title,
      description: '',
      precondition: '',
    },
    steps: [],
    test_data: [],
    validation: [],
  }
}

export function defaultApiStep(): ApiStep {
  return {
    name: '',
    domain: '',
    url: '',
    method: 'GET',
    headers: {},
    body: {},
    request_schema: null,
    response_schema: null,
    extract: [],
    assert: true,
  }
}

// ─── 单接口数据驱动格式（meta/request/cases）───
// 与后端 schema_config.py 的 SINGLE_API_SCHEMA 对齐。
// 前端通过 config_json 顶层 key 探测：有 "meta" → 单格式，有 "case_info" → 多格式。

export interface CaseMeta {
  title: string
  description: string
  base_url: string
  auth: AuthConfig | null
}

export interface AuthConfig {
  type: 'none' | 'bearer' | 'basic' | 'api_key'
  token?: string
  username?: string
  password?: string
  key?: string
  value?: string
}

/** 行级鉴权：不允许 type:none（用 null 表示不覆盖） */
export type RowAuthConfig = Omit<AuthConfig, 'type'> & {
  type: 'bearer' | 'basic' | 'api_key'
}

export interface ApiRequest {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH' | 'HEAD' | 'OPTIONS'
  path: string
  headers: Record<string, string>
}

export interface CaseInput {
  headers: Record<string, string>
  body: Record<string, unknown>
  auth: RowAuthConfig | null
}

export interface CaseExpect {
  status: number
  headers_schema: Record<string, unknown> | null
  body_schema: Record<string, unknown> | null
}

export interface ApiCase {
  id: string
  category: string
  scenario: string
  description: string
  input: CaseInput
  expect: CaseExpect
}

export interface SingleApiConfig {
  meta: CaseMeta
  request: ApiRequest
  cases: ApiCase[]
}

/** 格式探测：有 meta key → 单接口格式 */
export function isSingleFormat(config: Record<string, unknown> | null | undefined): boolean {
  if (!config || typeof config !== 'object') return false
  return 'meta' in config && 'cases' in config
}

export function defaultSingleApiConfig(title = ''): SingleApiConfig {
  return {
    meta: {
      title,
      description: '',
      base_url: '',
      auth: { type: 'none' },
    },
    request: {
      method: 'GET',
      path: '',
      headers: {},
    },
    cases: [],
  }
}
