import type { DeviceRecord } from "@/shared/types/device"

export const RUNNER_OCCUPIED_PREFIXES: string[] = ["ai_agent", "runner-", "task-", "run-"]

export function isRunnerOccupied(occupiedBy?: string | null): boolean {
  if (!occupiedBy) return false
  return RUNNER_OCCUPIED_PREFIXES.some((prefix) => occupiedBy.startsWith(prefix))
}

export function isExecutionOccupied(device: Pick<DeviceRecord, "status" | "occupied_by">): boolean {
  return device.status === "BUSY" && isRunnerOccupied(device.occupied_by)
}
