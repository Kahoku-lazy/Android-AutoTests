import client, { type DjangoResponse } from "@/shared/api-client"
import type {
  OpsAgent,
  OpsAgentInput,
  OpsModelConfig,
  OpsModelConfigInput,
  OpsBatchDisableResult,
  OpsPurgeResult,
  OpsUser,
  OpsUserListParams,
  OpsUserPage,
} from "./types"

export function listOpsUsers(
  params: OpsUserListParams,
): Promise<{ data: DjangoResponse<OpsUserPage> }> {
  return client.get("/ops/users/", { params })
}

export function setOpsUserActive(
  userId: number,
  active: boolean,
): Promise<{ data: DjangoResponse<{ user: OpsUser }> }> {
  return client.post(`/ops/users/${userId}/${active ? "enable" : "disable"}/`)
}

export function setOpsUserOperator(
  userId: number,
  enabled: boolean,
): Promise<{ data: DjangoResponse<{ user: OpsUser }> }> {
  return client.post(`/ops/users/${userId}/${enabled ? "grant-operator" : "revoke-operator"}/`)
}

export function listOpsAgents(): Promise<{ data: DjangoResponse<OpsAgent[]> }> {
  return client.get("/ai/roles/")
}

export function createOpsAgent(
  payload: OpsAgentInput,
): Promise<{ data: DjangoResponse<OpsAgent> }> {
  return client.post("/ai/roles/", payload)
}

export function updateOpsAgent(
  roleId: string,
  payload: OpsAgentInput,
): Promise<{ data: DjangoResponse<OpsAgent> }> {
  return client.patch(`/ai/roles/${roleId}/`, payload)
}

export function listModelConfigs(): Promise<{
  data: DjangoResponse<{ configs: OpsModelConfig[] }>
}> {
  return client.get("/ai/model-configs/")
}

export function discoverModelNames(payload: OpsModelConfigInput): Promise<{
  data: DjangoResponse<{ models: string[]; source: string; reason: string }>
}> {
  return client.post("/ai/model-configs/discover/", payload)
}

export function createModelConfig(
  payload: OpsModelConfigInput,
): Promise<{ data: DjangoResponse<OpsModelConfig> }> {
  return client.post("/ai/model-configs/", payload)
}

export function updateModelConfig(
  configId: number,
  payload: Partial<OpsModelConfigInput>,
): Promise<{ data: DjangoResponse<OpsModelConfig> }> {
  return client.patch(`/ai/model-configs/${configId}/`, payload)
}

export function deleteModelConfig(
  configId: number,
): Promise<{ data: DjangoResponse<Record<string, never>> }> {
  return client.delete(`/ai/model-configs/${configId}/`)
}

export function deleteOpsAgent(
  roleId: string,
): Promise<{ data: DjangoResponse<{ role_id: string }> }> {
  return client.delete(`/ai/roles/${roleId}/`)
}

export function disableOpsUsers(
  userIds: number[],
): Promise<{ data: DjangoResponse<OpsBatchDisableResult> }> {
  return client.post("/ops/users/disable/", { user_ids: userIds })
}

export function purgeOpsUsers(
  userIds: number[],
): Promise<{ data: DjangoResponse<OpsPurgeResult> }> {
  return client.post("/ops/users/purge/", { user_ids: userIds })
}

export function resetOpsUserPassword(
  userId: number,
): Promise<{ data: DjangoResponse<{ username: string; password: string }> }> {
  return client.post(`/ops/users/${userId}/reset-password/`)
}
