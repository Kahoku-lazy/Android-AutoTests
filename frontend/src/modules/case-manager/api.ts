/**
 * case-manager API — backward-compatible re-export facade.
 * Real implementations in api/ sub-directory.
 */
import client from "@/shared/api-client";

// ── 操作类型（跨平台统一）──

export function fetchStepTypes(target) {
  return client.get(`/cases/step-types?target=${target}`);
}

// Directories
export {
  fetchDirectories,
  createDirectory,
  updateDirectory,
  deleteDirectory,
  batchMoveItems,
  setDirectoryPermission,
} from "./api/directories.js";

// UI Automation
export {
  listDefinitions,
  getDefinition,
  saveDefinition,
  deleteDefinition,
  batchImportDefinitions,
  exportYaml,
  listExports,
  acquireEditLock,
  releaseEditLock,
  caseLock,
  caseUnlock,
  setVisibility,
  listDevices,
  listPages,
  getPageElements,
  runStep,
} from "./api/uiAutomation.js";

// Storage
export {
  listStorageDefinitions,
  getStorageDefinition,
  saveStorageDefinition,
  deleteStorageDefinition,
  batchImportStorageDefinitions,
} from "./api/storage.js";

// API Testing
export {
  listApiDefinitions,
  getApiDefinition,
  saveApiDefinition,
  deleteApiDefinition,
  batchImportApiDefinitions,
} from "./api/apiTesting.js";

// Web Automation
export {
  listWebDefinitions,
  getWebDefinition,
  saveWebDefinition,
  deleteWebDefinition,
  batchImportWebDefinitions,
} from "./api/webAutomation.js";
