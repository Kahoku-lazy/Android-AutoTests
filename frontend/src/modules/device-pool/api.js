/** device-pool API client functions — 12 endpoints */
import client from '@/shared/api-client.js'

export function apiListDevices() {
  return client.get('/devices')
}

export function apiScanDevices(target) {
  return client.post('/devices/scan', target ? { target } : {})
}

export function apiConnectDevice(serial, { activate = true, userId, timeout } = {}) {
  return client.post(`/devices/${serial}`, {
    activate,
    user_id: userId || '',
    timeout: timeout || 300,
  })
}

export function apiGetCurrent() {
  return client.get('/devices/current')
}

export function apiActivate(serial) {
  return client.post(`/devices/${serial}/activate`)
}

export function apiLockDevice(serial, userId, timeout = 300, type = "user") {
  return client.post(`/devices/${serial}/lock`, {
    user_id: userId,
    timeout,
    type,
  })
}

export function apiReleaseDevice(serial, { userId, reason = 'manual', unlock = false, force = false } = {}) {
  return client.post(`/devices/${serial}/release`, {
    user_id: userId || '',
    reason,
    unlock,
    force,
  })
}

export function apiDisconnect(serial, { force = false, reason = '', userId, isAdmin } = {}) {
  return client.post(`/devices/${serial}/disconnect`, {
    force,
    reason,
    user_id: userId || '',
    is_admin: isAdmin || false,
  })
}

export function apiGetQueue() {
  return client.get('/devices/queue')
}

export function apiJoinQueue(serial, userId) {
  return client.post(`/devices/${serial}/queue`, { user_id: userId })
}

export function apiLeaveQueue(serial, userId) {
  return client.post(`/devices/${serial}/queue/leave`, { user_id: userId || '' })
}

export function apiHeartbeat() {
  return client.get('/devices/heartbeat')
}
