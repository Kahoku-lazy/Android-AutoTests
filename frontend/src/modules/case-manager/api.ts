/** case-manager API — 项目 / 目录 / 文件 / 文档用例（DRF {status,data} 信封） */
import client from '@/shared/api-client'
import type { DjangoResponse } from '@/shared/api-client'
import type {
  CaseDefinition,
  CaseFileMeta,
  CaseFileSheet,
  CaseProject,
  ProjectTreePayload,
  BusinessType,
  TestType,
} from './types'

type Envelope<T> = Promise<{ data: DjangoResponse<T> }>

// ── Projects ──

export function listProjects(): Envelope<CaseProject[]> {
  return client.get<DjangoResponse<CaseProject[]>>('/cases/projects/')
}

export function createProject(body: { name: string; description?: string }): Envelope<CaseProject> {
  return client.post<DjangoResponse<CaseProject>>('/cases/projects/', body)
}

export function updateProject(
  id: number,
  body: { name?: string; description?: string },
): Envelope<CaseProject> {
  return client.patch<DjangoResponse<CaseProject>>(`/cases/projects/${id}/`, body)
}

export function deleteProject(id: number): Envelope<{ id: number }> {
  return client.delete<DjangoResponse<{ id: number }>>(`/cases/projects/${id}/`)
}

export function getProjectTree(projectId: number): Envelope<ProjectTreePayload> {
  return client.get<DjangoResponse<ProjectTreePayload>>(`/cases/projects/${projectId}/tree/`)
}

// ── Directories ──

export function createDirectory(body: {
  project_id: number
  name: string
  parent_id?: number | null
  sort_order?: number
}): Envelope<Record<string, unknown>> {
  return client.post<DjangoResponse<Record<string, unknown>>>('/cases/directories/', body)
}

export function updateDirectory(
  id: number,
  body: { name?: string; sort_order?: number },
): Envelope<Record<string, unknown>> {
  return client.patch<DjangoResponse<Record<string, unknown>>>(`/cases/directories/${id}/`, body)
}

export function deleteDirectory(id: number): Envelope<{ id: number }> {
  return client.delete<DjangoResponse<{ id: number }>>(`/cases/directories/${id}/`)
}

// ── Files (Excel sheets) ──

export function createFile(body: {
  project_id: number
  name: string
  directory_id?: number | null
  sort_order?: number
}): Envelope<CaseFileMeta> {
  return client.post<DjangoResponse<CaseFileMeta>>('/cases/files/', body)
}

export function getFileSheet(fileId: number): Envelope<CaseFileSheet> {
  return client.get<DjangoResponse<CaseFileSheet>>(`/cases/files/${fileId}/`)
}

export function updateFile(
  id: number,
  body: { name?: string; sort_order?: number },
): Envelope<CaseFileMeta> {
  return client.patch<DjangoResponse<CaseFileMeta>>(`/cases/files/${id}/`, body)
}

export function deleteFile(id: number): Envelope<{ id: number }> {
  return client.delete<DjangoResponse<{ id: number }>>(`/cases/files/${id}/`)
}

// ── Definitions (rows) ──

export function createDefinition(body: {
  project_id: number
  file_id: number
  title?: string
  test_type?: TestType
  business_type?: BusinessType
  module?: string
  precondition?: string
  steps?: string
  expected_result?: string
  sort_order?: number
  require_fields?: boolean
}): Envelope<CaseDefinition> {
  return client.post<DjangoResponse<CaseDefinition>>('/cases/definitions/', body)
}

export function getDefinition(id: string): Envelope<CaseDefinition> {
  return client.get<DjangoResponse<CaseDefinition>>(`/cases/definitions/${id}/`)
}

export function updateDefinition(
  id: string,
  body: Partial<{
    title: string
    test_type: TestType
    business_type: BusinessType
    module: string
    precondition: string
    steps: string
    expected_result: string
    sort_order: number
    require_fields: boolean
  }>,
): Envelope<CaseDefinition> {
  return client.patch<DjangoResponse<CaseDefinition>>(`/cases/definitions/${id}/`, body)
}

export function deleteDefinition(id: string): Envelope<{ id: string }> {
  return client.delete<DjangoResponse<{ id: string }>>(`/cases/definitions/${id}/`)
}

export function batchDeleteDefinitions(ids: string[]): Envelope<{ deleted: number }> {
  return client.post<DjangoResponse<{ deleted: number }>>('/cases/definitions/batch-delete/', {
    ids,
  })
}

// ── Move ──

export function moveItem(body: {
  project_id: number
  item_type: 'directory' | 'file'
  item_id: number | string
  target_directory_id?: number | null
  sort_order?: number
}): Envelope<Record<string, unknown>> {
  return client.post<DjangoResponse<Record<string, unknown>>>('/cases/move/', body)
}
