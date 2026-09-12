/** Device-Pool 工具函数 — 纯函数，从 constants.ts 拆分 */
import type { DeviceRecord, DeviceStatusMeta } from '@/shared/types/device'
import { ADB_PORT_MAX, ADB_PORT_MIN, DEVICE_STATUS_MAP, IPV4_RE } from './constants'

export type LanConnectPayload = {
  target: string
  pair_port?: string
  pair_code?: string
}

export type LanConnectErrors = {
  ip: string
  connectPort: string
  pairPort: string
  pairCode: string
}

export type LanConnectFields = {
  ip: string
  connectPort: string
  pairPort: string
  pairCode: string
}

function portError(raw: string, emptyMsg: string): string {
  const val = raw.trim()
  if (!val) return emptyMsg
  if (!/^\d+$/.test(val)) return `端口需为 ${ADB_PORT_MIN}-${ADB_PORT_MAX} 的整数`
  const num = Number(val)
  if (num < ADB_PORT_MIN || num > ADB_PORT_MAX) {
    return `端口需为 ${ADB_PORT_MIN}-${ADB_PORT_MAX} 的整数`
  }
  return ''
}

export function validateLanConnect(fields: LanConnectFields): {
  ok: boolean
  errors: LanConnectErrors
  payload?: LanConnectPayload
  firstError?: keyof LanConnectErrors
} {
  const errors: LanConnectErrors = { ip: '', connectPort: '', pairPort: '', pairCode: '' }
  const ip = fields.ip.trim()
  if (!ip) errors.ip = '请输入 IP 地址'
  else if (!IPV4_RE.test(ip)) errors.ip = '请输入合法的 IPv4 地址（如 10.162.95.96）'
  errors.connectPort = portError(fields.connectPort, '请输入连接端口')

  const pairPort = fields.pairPort.trim()
  const pairCode = fields.pairCode.trim()
  const pairPartial = Boolean(pairPort || pairCode)
  if (pairPartial) {
    errors.pairPort = portError(fields.pairPort, '请输入配对端口')
    if (!pairCode) errors.pairCode = '请输入配对码'
    else if (!/^\d{4,16}$/.test(pairCode)) errors.pairCode = '配对码为 4-16 位数字'
  }

  const order: (keyof LanConnectErrors)[] = ['ip', 'connectPort', 'pairPort', 'pairCode']
  const firstError = order.find((k) => errors[k])
  if (firstError) return { ok: false, errors, firstError }
  const payload: LanConnectPayload = {
    target: `${ip}:${fields.connectPort.trim()}`,
  }
  if (pairPartial) {
    payload.pair_port = pairPort
    payload.pair_code = pairCode
  }
  return { ok: true, errors, payload }
}

export function formatRelativeTime(iso: string): string {
  if (!iso) return '—'
  const diff = Date.now() - new Date(iso).getTime()
  const sec = Math.floor(diff / 1000)
  if (sec < 60) return '刚刚'
  if (sec < 3600) return `${Math.floor(sec / 60)} 分钟前`
  if (sec < 86400) return `${Math.floor(sec / 3600)} 小时前`
  return new Date(iso).toLocaleDateString('zh-CN')
}

export function formatDateTime(iso: string): string {
  // 绝对时间：YYYY-MM-DD HH:mm:ss（设备连接时间点）
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return '—'
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

export function displayModel(device: DeviceRecord): string {
  const parts: string[] = []
  if (device.brand) parts.push(device.brand)
  if (device.model) parts.push(device.model)
  return parts.length ? parts.join(' ') : '—'
}

export function connectionLabel(record: DeviceRecord): string {
  if (record.connection_type === 'WIFI') {
    return `局域网连接：${record.connection_addr || record.serial}`
  }
  return 'USB 有线'
}

export function deviceAddress(record: DeviceRecord): string {
  // 原始 adb devices 传输地址：无线为 connection_addr，USB 即序列号本身
  return record.connection_addr || record.serial
}

export function statusTag(status: string): DeviceStatusMeta {
  return DEVICE_STATUS_MAP[status] || { type: 'info', text: status }
}
