/**
 * 设备列表查询：与设备管理页同一份数据源（`GET /api/devices/`）。
 *
 * 只给需要「选一台设备」的模块用（任务清单、SOP 运行弹窗），
 * 不在各模块里另建一套设备数据。
 */

import djangoClient from "@/shared/api-client"
import type { DeviceListResponse, DeviceRecord } from "@/shared/types/device"

/**
 * 取当前设备的可连列表。
 *
 * Returns:
 *   设备记录数组；接口不可用时返回空数组，由调用方决定「不选设备」还是拦住。
 */
export async function listDevices(): Promise<DeviceRecord[]> {
  const { data } = await djangoClient.get<DeviceListResponse>("/devices/")
  return data.data?.devices || []
}
