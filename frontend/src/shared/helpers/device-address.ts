const IP_PORT = /^\d{1,3}(?:\.\d{1,3}){3}:\d+$/
const TLS_ALIAS = "_adb-tls-connect._tcp"

export interface DeviceRef {
  serial: string
  connection_addr?: string
  model?: string
  status?: string
}

export function deviceAddress(device: DeviceRef): string {
  const addr = (device.connection_addr || "").trim()
  if (IP_PORT.test(addr)) return addr
  return device.serial
}

export function isSelectableDevice(device: DeviceRef): boolean {
  return !(device.connection_addr || "").includes(TLS_ALIAS)
}

export function deviceLabel(device: DeviceRef): string {
  const address = deviceAddress(device)
  const model = (device.model || "").trim()
  const head = model ? `${address} · ${model}` : address
  const status = (device.status || "").trim()
  return status && status !== "ONLINE" ? `${head} (${status})` : head
}
