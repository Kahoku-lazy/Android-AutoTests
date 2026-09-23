/**
 * 「设备被执行引擎占用」判定的唯一登记处。
 *
 * 占用者前缀是跨模块口径（设备管理页与设备检查器共用）：由执行引擎发起的占用
 * 用这些前缀标识，新增前缀只在这里登记一次，模块内不得再复制前缀清单。
 */
import type { DeviceRecord } from "@/shared/types/device"

/** 执行引擎占用者的前缀清单（唯一登记处） */
export const RUNNER_OCCUPIED_PREFIXES: string[] = ["ai_agent", "runner-", "task-", "run-"]

/** `occupied_by` 是否由执行引擎发起（只看前缀，不判设备状态） */
export function isRunnerOccupied(occupiedBy?: string | null): boolean {
  if (!occupiedBy) return false
  return RUNNER_OCCUPIED_PREFIXES.some((prefix) => occupiedBy.startsWith(prefix))
}

/** 设备此刻是否正被执行引擎占用（`BUSY` + 执行引擎前缀） */
export function isExecutionOccupied(device: Pick<DeviceRecord, "status" | "occupied_by">): boolean {
  return device.status === "BUSY" && isRunnerOccupied(device.occupied_by)
}
