/** 新建任务提交给执行器的 adb 地址：USB 序列号或 IP:端口。 */

const IP_PORT = /^\d{1,3}(?:\.\d{1,3}){3}:\d+$/
const TLS_ALIAS = "_adb-tls-connect._tcp"

export interface TaskDeviceRef {
  serial: string
  connection_addr?: string
  model?: string
  status?: string
}

/** 连接地址是 IP:端口时用它，否则用 USB 序列号。 */
export function taskDeviceAddress(device: TaskDeviceRef): string {
  const addr = (device.connection_addr || "").trim()
  if (IP_PORT.test(addr)) return addr
  return device.serial
}

/** 只挂在无线调试别名上的记录不能选。 */
export function isSelectableTaskDevice(device: TaskDeviceRef): boolean {
  return !(device.connection_addr || "").includes(TLS_ALIAS)
}

/** 下拉文案：可连地址，有型号时附在后面。 */
export function taskDeviceLabel(device: TaskDeviceRef): string {
  const address = taskDeviceAddress(device)
  const model = (device.model || "").trim()
  const status = device.status || ""
  const head = model ? `${address} · ${model}` : address
  return status ? `${head} (${status})` : head
}
