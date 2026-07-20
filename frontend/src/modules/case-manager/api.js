/**
 * case-manager API — 用例管理模块
 */
import client from "@/shared/api-client.js";

// ── 目录管理 ──

export function fetchDirectories() {
  return client.get("/cases/directories");
}

export function createDirectory(name, parentId) {
  return client.post("/cases/directories/create", {
    name,
    parent_id: parentId,
  });
}

export function updateDirectory(id, data) {
  return client.post(`/cases/directories/${id}`, data);
}

export function deleteDirectory(id) {
  return client.post(`/cases/directories/${id}`, { action: "delete" });
}

// ── 用例定义 ──

export function listDefinitions(directoryId) {
  const params = directoryId ? `?directory_id=${directoryId}` : "";
  return client.get(`/cases/definitions${params}`);
}

export function getDefinition(id) {
  return client.get(`/cases/definitions/${id}`);
}

export function saveDefinition(form) {
  return client.post("/cases/definitions", form);
}

export function deleteDefinition(id) {
  return client.delete(`/cases/definitions/${id}`);
}

// ── 编辑锁 ──

export function acquireEditLock(caseId) {
  return client.post(`/cases/definitions/${caseId}/lock`);
}

export function releaseEditLock(caseId, force = false) {
  return client.post(`/cases/definitions/${caseId}/unlock`, { force });
}

// ── 用例持久锁（创建者控制）──

export function caseLock(caseId) {
  return client.post(`/cases/definitions/${caseId}/case-lock`);
}

export function caseUnlock(caseId) {
  return client.post(`/cases/definitions/${caseId}/case-unlock`);
}

export function setVisibility(caseId, visibility, permittedUsers = []) {
  return client.post(`/cases/definitions/${caseId}/visibility`, { visibility, permitted_users: permittedUsers });
}

export function setDirectoryPermission(dirId, allowCreate, allowDelete) {
  return client.post(`/cases/directories/${dirId}/permission`, { allow_create: allowCreate, allow_delete: allowDelete });
}

// ── YAML 导出 ──

export function exportYaml(testCaseName) {
  return client.post("/cases/export/yaml", {
    test_case_name: testCaseName || "auto_test",
  });
}

export function listExports() {
  return client.get("/cases/exports");
}

// ── 批量移动 ──

export function batchMoveItems(items, targetDirectoryId) {
  return client.post("/cases/directories/batch-move", {
    items,
    target_directory_id: targetDirectoryId,
  });
}

// ── 批量导入（PRD 用例设计 → 入库）──

export function batchImportDefinitions(cases, options = {}) {
  return client.post("/cases/definitions/batch", {
    cases,
    overwrite: options.overwrite || false,
    directory_id: options.directoryId || null,
    package_name: options.packageName || "",
  });
}

// ── 设备（跨模块，调试用）──

export function listDevices() {
  return client.get("/devices");
}

// ── 元素库（跨模块，步骤编辑器用）──

export function listPages() {
  return client.get("/elements/pages");
}

export function getPageElements(pageId) {
  return client.get(`/elements/pages/${pageId}/items`);
}

// ── 单步调试（跨模块）──

export function runStep(params) {
  return client.post("/runner/run-step", params);
}
