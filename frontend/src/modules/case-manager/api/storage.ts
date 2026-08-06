/**
 * case-manager storage/business function test case API
 */
import client from "@/shared/api-client";

export function listStorageDefinitions(directoryId) {
  const params = directoryId ? `?directory_id=${directoryId}` : "";
  return client.get(`/cases/storage/definitions${params}`);
}

export function getStorageDefinition(id) {
  return client.get(`/cases/storage/definitions/${id}`);
}

export function saveStorageDefinition(form) {
  return client.post("/cases/storage/definitions", form);
}

export function deleteStorageDefinition(id) {
  return client.delete(`/cases/storage/definitions/${id}`);
}

export function batchImportStorageDefinitions(cases, options = {}) {
  return client.post("/cases/storage/definitions/batch", {
    cases,
    overwrite: options.overwrite || false,
    directory_id: options.directoryId || null,
  });
}
