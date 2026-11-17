/**
 * 设备下拉的值口径：任务与 SOP 运行共用同一套「提交给执行器的 adb 地址」。
 *
 * - USB 设备提交硬件序列号；
 * - 局域网设备提交 `IP:端口`（库内硬件序列号在无线调试下连不上）；
 * - 只挂在无线调试别名上的记录不可选。
 */

const IP_PORT = /^\d{1,3}(?:\.\d{1,3}){3}:\d+$/
const TLS_ALIAS = "_adb-tls-connect._tcp"

export interface DeviceRef {
  serial: string
  connection_addr?: string
  model?: string
  status?: string
}

/** 连接地址是 IP:端口时用它，否则用 USB 序列号。 */
export function deviceAddress(device: DeviceRef): string {
  const addr = (device.connection_addr || "").trim()
  if (IP_PORT.test(addr)) return addr
  return device.serial
}

/** 只挂在无线调试别名上的记录不能选。 */
export function isSelectableDevice(device: DeviceRef): boolean {
  return !(device.connection_addr || "").includes(TLS_ALIAS)
}

/**
 * 下拉文案：可连地址，有型号时附在后面。
 *
 * 在线是下拉里的默认态（选项本来就按可连地址筛过），所以不拼 `(ONLINE)`——
 * 320px 的左列放不下，会截成 `… SM-G9730 (ON`。非在线状态仍然拼上，离线可辨。
 */
export function deviceLabel(device: DeviceRef): string {
  const address = deviceAddress(device)
  const model = (device.model || "").trim()
  const head = model ? `${address} · ${model}` : address
  const status = (device.status || "").trim()
  return status && status !== "ONLINE" ? `${head} (${status})` : head
}
