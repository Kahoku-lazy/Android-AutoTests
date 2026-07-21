/**
 * case-manager web automation test case API
 */
import client from "@/shared/api-client.js";

export function listWebDefinitions(directoryId) {
  const params = directoryId ? `?directory_id=${directoryId}` : "";
  return client.get(`/cases/web/definitions${params}`);
}

export function getWebDefinition(id) {
  return client.get(`/cases/web/definitions/${id}`);
}

export function saveWebDefinition(form) {
  return client.post("/cases/web/definitions", form);
}

export function deleteWebDefinition(id) {
  return client.delete(`/cases/web/definitions/${id}`);
}

export function batchImportWebDefinitions(cases, options = {}) {
  return client.post("/cases/web/definitions/batch", {
    cases,
    overwrite: options.overwrite || false,
    directory_id: options.directoryId || null,
  });
}
