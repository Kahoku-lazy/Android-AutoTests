/**
 * case-manager API interface test case API
 */
import client from "@/shared/api-client.js";

export function listApiDefinitions(directoryId) {
  const params = directoryId ? `?directory_id=${directoryId}` : "";
  return client.get(`/cases/api-testing/definitions${params}`);
}

export function getApiDefinition(id) {
  return client.get(`/cases/api-testing/definitions/${id}`);
}

export function saveApiDefinition(form) {
  return client.post("/cases/api-testing/definitions", form);
}

export function deleteApiDefinition(id) {
  return client.delete(`/cases/api-testing/definitions/${id}`);
}

export function batchImportApiDefinitions(cases, options = {}) {
  return client.post("/cases/api-testing/definitions/batch", {
    cases,
    overwrite: options.overwrite || false,
    directory_id: options.directoryId || null,
  });
}
