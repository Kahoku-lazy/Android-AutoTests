/** Device-Pool 工具函数 — 纯函数，从 constants.ts 拆分 */
import type { DeviceRecord, DeviceStatusMeta } from '@/shared/types/device'
import { DEVICE_STATUS_MAP } from './constants'

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
