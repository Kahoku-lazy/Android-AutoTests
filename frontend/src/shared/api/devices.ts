import djangoClient from "@/shared/api-client"
import type { DeviceListResponse, DeviceRecord } from "@/shared/types/device"

export async function listDevices(): Promise<DeviceRecord[]> {
  const { data } = await djangoClient.get<DeviceListResponse>("/devices/")
  return data.data?.devices || []
}
