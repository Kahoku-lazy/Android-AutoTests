/** 运营后台 API — 用户走 /api/ops/*，智能体走既有 /api/ai/agents/*。 */
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

/** 停用 / 启用：两个动作各一个端点，避免前端拼状态字段。 */
export function setOpsUserActive(
  userId: number,
  active: boolean,
): Promise<{ data: DjangoResponse<{ user: OpsUser }> }> {
  return client.post(`/ops/users/${userId}/${active ? "enable" : "disable"}/`)
}

/** 设为运营 / 取消运营：仅超管可调用，两个动作各一个端点。 */
export function setOpsUserOperator(
  userId: number,
  enabled: boolean,
): Promise<{ data: DjangoResponse<{ user: OpsUser }> }> {
  const action = enabled ? "grant-operator" : "revoke-operator"
  return client.post(`/ops/users/${userId}/${action}/`)
}

/** Agent 配置清单。 */
export function listOpsAgents(): Promise<{ data: DjangoResponse<OpsAgent[]> }> {
  return client.get("/ai/roles/")
}

/** 新建 Agent 配置：名称、模型配置、系统提示词。 */
export function createOpsAgent(
  payload: OpsAgentInput,
): Promise<{ data: DjangoResponse<OpsAgent> }> {
  return client.post("/ai/roles/", payload)
}

/** 修改 Agent 配置。 */
export function updateOpsAgent(
  roleId: string,
  payload: OpsAgentInput,
): Promise<{ data: DjangoResponse<OpsAgent> }> {
  return client.patch(`/ai/roles/${roleId}/`, payload)
}

/** 模型配置清单。智能体表单的两个下拉都从这里来。 */
export function listModelConfigs(): Promise<{
  data: DjangoResponse<{ configs: OpsModelConfig[] }>
}> {
  return client.get("/ai/model-configs/")
}

/** 向厂商查询模型名。查不到时 models 为空，页面改用手填。 */
export function discoverModelNames(payload: OpsModelConfigInput): Promise<{
  data: DjangoResponse<{ models: string[]; source: string; reason: string }>
}> {
  return client.post("/ai/model-configs/discover/", payload)
}

/** 新建模型配置。 */
export function createModelConfig(
  payload: OpsModelConfigInput,
): Promise<{ data: DjangoResponse<OpsModelConfig> }> {
  return client.post("/ai/model-configs/", payload)
}

/** 修改模型配置。 */
export function updateModelConfig(
  configId: number,
  payload: Partial<OpsModelConfigInput>,
): Promise<{ data: DjangoResponse<OpsModelConfig> }> {
  return client.patch(`/ai/model-configs/${configId}/`, payload)
}

/** 删除模型配置。已被智能体使用时后端拒绝。 */
export function deleteModelConfig(
  configId: number,
): Promise<{ data: DjangoResponse<Record<string, never>> }> {
  return client.delete(`/ai/model-configs/${configId}/`)
}

/** 删除智能体。后端会一并删除它名下的任务。 */
export function deleteOpsAgent(
  roleId: string,
): Promise<{ data: DjangoResponse<{ role_id: string }> }> {
  return client.delete(`/ai/roles/${roleId}/`)
}

/** 本页批量停用。不可管理的行在结果里逐行拒绝。 */
export function disableOpsUsers(
  userIds: number[],
): Promise<{ data: DjangoResponse<OpsBatchDisableResult> }> {
  return client.post("/ops/users/disable/", { user_ids: userIds })
}

/** 批量注销。仅超管；只删账号，不删业务数据。 */
export function purgeOpsUsers(
  userIds: number[],
): Promise<{ data: DjangoResponse<OpsPurgeResult> }> {
  return client.post("/ops/users/purge/", { user_ids: userIds })
}

/** 重置密码：一次性密码只在这次响应里返回。 */
export function resetOpsUserPassword(
  userId: number,
): Promise<{ data: DjangoResponse<{ username: string; password: string }> }> {
  return client.post(`/ops/users/${userId}/reset-password/`)
}
