/** case-manager API — 项目表、导入与个人视图。 */
import client from "@/shared/api-client"
import type { DjangoResponse } from "@/shared/api-client"
import type { CaseProject, CaseRow, LibraryKind, ProjectSheet, SheetView } from "./types"

type Envelope<T> = Promise<{ data: DjangoResponse<T> }>

export function listProjects(): Envelope<CaseProject[]> {
  return client.get<DjangoResponse<CaseProject[]>>("/cases/projects/")
}

export function createProject(body: {
  name: string
  description?: string
  library_kind: LibraryKind
}): Envelope<CaseProject> {
  return client.post<DjangoResponse<CaseProject>>("/cases/projects/", body)
}

export function deleteProject(id: number): Envelope<{ id: number }> {
  return client.delete<DjangoResponse<{ id: number }>>(`/cases/projects/${id}/`)
}

export function getProjectSheet(projectId: number): Envelope<ProjectSheet> {
  return client.get<DjangoResponse<ProjectSheet>>(`/cases/projects/${projectId}/`)
}

export function createRow(
  projectId: number,
  body: Partial<CaseRow> & { title: string; steps: CaseRow["steps"] },
): Envelope<CaseRow> {
  return client.post<DjangoResponse<CaseRow>>(`/cases/projects/${projectId}/rows/`, body)
}

export function updateRow(
  projectId: number,
  caseId: string,
  body: Partial<CaseRow>,
): Envelope<CaseRow> {
  return client.patch<DjangoResponse<CaseRow>>(`/cases/projects/${projectId}/rows/${caseId}/`, body)
}

export function deleteRow(projectId: number, caseId: string): Envelope<{ id: string }> {
  return client.delete<DjangoResponse<{ id: string }>>(
    `/cases/projects/${projectId}/rows/${caseId}/`,
  )
}

export function importProjectYaml(projectId: number, file: File): Envelope<{ imported: number }> {
  const body = new FormData()
  body.set("file", file)
  return client.post<DjangoResponse<{ imported: number }>>(
    `/cases/projects/${projectId}/import-yaml/`,
    body,
    { headers: { "Content-Type": "multipart/form-data" } },
  )
}

export function saveSheetView(projectId: number, view: SheetView): Envelope<SheetView> {
  return client.put<DjangoResponse<SheetView>>(`/cases/projects/${projectId}/view/`, view)
}
