/** 运营后台 · 用户管理 API — 唯一 HTTP 出口，统一走 /api/ops/* */
import client, { type DjangoResponse } from "@/shared/api-client"
import type { OpsUser, OpsUserListParams, OpsUserPage } from "./types"

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

/** 重置密码：一次性密码只在这次响应里返回。 */
export function resetOpsUserPassword(
  userId: number,
): Promise<{ data: DjangoResponse<{ username: string; password: string }> }> {
  return client.post(`/ops/users/${userId}/reset-password/`)
}
