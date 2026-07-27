/**
 * case-manager UI automation case API
 */
import client from "@/shared/api-client.js";

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

export function batchImportDefinitions(cases, options = {}) {
  return client.post("/cases/definitions/batch", {
    cases,
    overwrite: options.overwrite || false,
    directory_id: options.directoryId || null,
    package_name: options.packageName || "",
  });
}

export function exportYaml(testCaseName) {
  return client.post("/cases/export/yaml", { test_case_name: testCaseName || "auto_test" });
}

export function listExports() {
  return client.get("/cases/exports");
}

// ── Lock & Visibility (shared across types) ──

export function acquireEditLock(caseId) {
  return client.post(`/cases/definitions/${caseId}/lock`);
}

export function releaseEditLock(caseId, force = false) {
  return client.post(`/cases/definitions/${caseId}/unlock`, { force });
}

export function caseLock(caseId) {
  return client.post(`/cases/definitions/${caseId}/case-lock`);
}

export function caseUnlock(caseId) {
  return client.post(`/cases/definitions/${caseId}/case-unlock`);
}

export function setVisibility(caseId, visibility, permittedUsers = []) {
  return client.post(`/cases/definitions/${caseId}/visibility`, {
    visibility,
    permitted_users: permittedUsers,
  });
}

// ── Cross-module helpers ──

export function listDevices() {
  return client.get("/devices");
}

export function connectDebugDevice(serial) {
  return client.post(`/devices/${serial}`, { activate: true, mode: "observe" });
}

export function disconnectDebugDevice(serial) {
  return client.post(`/devices/${serial}/disconnect-observe`);
}

export function listPages() {
  return client.get("/elements/pages");
}

export function getPageElements(pageId) {
  return client.get(`/elements/pages/${pageId}/items`);
}

export function runStep(params) {
  return client.post("/runner/run-step", params);
}
