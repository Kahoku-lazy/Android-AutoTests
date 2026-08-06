/**
 * case-manager directory API
 */
import client from "@/shared/api-client";

export function fetchDirectories(caseType = null) {
  const params = caseType ? `?case_type=${caseType}` : "";
  return client.get(`/cases/directories${params}`);
}

export function createDirectory(name, parentId, caseType = "ui_automation") {
  return client.post("/cases/directories/create", {
    name,
    parent_id: parentId,
    case_type: caseType,
  });
}

export function updateDirectory(id, data) {
  return client.post(`/cases/directories/${id}`, data);
}

export function deleteDirectory(id) {
  return client.post(`/cases/directories/${id}`, { action: "delete" });
}

export function batchMoveItems(items, targetDirectoryId) {
  return client.post("/cases/directories/batch-move", { items, target_directory_id: targetDirectoryId });
}

export function setDirectoryPermission(dirId, allowCreate, allowDelete) {
  return client.post(`/cases/directories/${dirId}/permission`, {
    allow_create: allowCreate,
    allow_delete: allowDelete,
  });
}
