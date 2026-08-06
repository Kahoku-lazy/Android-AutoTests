/** Device-Pool 工具函数 — 纯函数，从 constants.ts 拆分 */
import type { DeviceRecord, DeviceStatusMeta } from '@/shared/types/device'
import { DEVICE_STATUS_MAP, CONNECTION_TYPE_LABEL } from './constants'

export function formatRelativeTime(iso: string): string {
  if (!iso) return '—'
  const diff = Date.now() - new Date(iso).getTime()
  const sec = Math.floor(diff / 1000)
  if (sec < 60) return '刚刚'
  if (sec < 3600) return `${Math.floor(sec / 60)} 分钟前`
  if (sec < 86400) return `${Math.floor(sec / 3600)} 小时前`
  return new Date(iso).toLocaleDateString('zh-CN')
}

export function displayModel(device: DeviceRecord): string {
  const parts: string[] = []
  if (device.brand) parts.push(device.brand)
  if (device.model) parts.push(device.model)
  return parts.length ? parts.join(' ') : '—'
}

export function connectionLabel(type: string): string {
  return CONNECTION_TYPE_LABEL[type] || type || '—'
}

export function statusTag(status: string): DeviceStatusMeta {
  return DEVICE_STATUS_MAP[status] || { type: 'info', text: status }
}
