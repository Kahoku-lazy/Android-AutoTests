/**
 * useDeviceActions — 设备操作逻辑提取
 *
 * 从 index.vue 提取所有设备操作 handler、心跳轮询、数据加载、动画逻辑。
 * 依赖 Pinia store（跨组件共享）和 constants.js。
 */
import { ref, nextTick } from 'vue'
import { animate, stagger } from 'animejs'
import { ElMessage } from 'element-plus'
import {
  HEARTBEAT_INTERVAL, RUNNER_OCCUPIED_PREFIXES,
  DEFAULT_DIALOGS, LIST_ANIMATION,
} from '../constants.js'

/**
 * @param {ReturnType<typeof import('../store.js').useDevicePoolStore>} store — Pinia store 实例
 */
export function useDeviceActions(store) {
  // ── Dialog state ──
  const disconnectDialog = ref({ ...DEFAULT_DIALOGS.disconnect })
  const networkDialog = ref({ ...DEFAULT_DIALOGS.network })

  // ── Internal state ──
  let heartbeatTimer = null
  let prevDevicesJson = ''

  // ── Current user ──
  function getCurrentUser() {
    const active = sessionStorage.getItem('auth_active') || ''
    if (active) return active
    try {
      const pool = JSON.parse(localStorage.getItem('auth_accounts') || '{}')
      return Object.keys(pool)[0] || ''
    } catch { return '' }
  }
  const currentUser = getCurrentUser()

  // ── Animation ──
  function animateDeviceRows() {
    animate(LIST_ANIMATION.selector, {
      opacity: LIST_ANIMATION.opacity,
      translateY: LIST_ANIMATION.translateY,
      delay: stagger(LIST_ANIMATION.staggerDelay),
      duration: LIST_ANIMATION.duration,
      ease: LIST_ANIMATION.ease,
    })
  }

  // ── Data loading ──
  async function loadDevices() {
    await store.fetchDevices()
    await nextTick()
    const json = JSON.stringify(store.devices)
    if (json !== prevDevicesJson) {
      prevDevicesJson = json
      animateDeviceRows()
    }
  }

  // ── Heartbeat ──
  function startHeartbeat() {
    stopHeartbeat()
    heartbeatTimer = setInterval(async () => {
      await store.doHeartbeat()
      loadDevices()
    }, HEARTBEAT_INTERVAL)
  }

  function stopHeartbeat() {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }
  }

  // ── Refresh / Scan ──
  async function handleRefresh() {
    if (store.scanning || store.loading) return
    const result = await store.doScan()
    if (result && result.ok) {
      ElMessage.success(`扫描完成，发现 ${result.count || 0} 台设备`)
    } else if (result && !result.ok) {
      ElMessage.error(result.error || '扫描失败')
    }
    await loadDevices()
  }

  // ── Network (LAN) connect ──
  function openNetworkDialog() {
    networkDialog.value = { visible: true, loading: false }
  }

  async function handleNetworkConnect({ target }) {
    if (!target) return
    networkDialog.value.loading = true
    const result = await store.doScan(target)
    networkDialog.value.loading = false
    if (result && result.ok) {
      ElMessage.success(`已连接 ${target}`)
      networkDialog.value.visible = false
      await loadDevices()
    } else {
      ElMessage.error((result && result.error) || '连接失败')
    }
  }

  function cancelNetworkDialog() {
    networkDialog.value.visible = false
  }

  // ── Row click ──
  function handleRowClick(record) {
    if (!record || !record.serial) return
    const dev = store.devices.find((d) => d.serial === record.serial)
    if (!dev) return
    if (dev.status === 'OFFLINE' || dev.status === 'DISCONNECTED') return
    store.selectDevice(record.serial)
  }

  // ── Lock / Unlock ──
  async function handleLockClick(device) {
    if (device.locked_by) {
      if (device.locked_by !== currentUser) {
        ElMessage.warning(`设备已被 ${device.locked_by} 锁定，只有锁定者可以解除`)
        return
      }
      const result = await store.doRelease(device.serial, {
        unlock: true, reason: 'manual', userId: currentUser,
      })
      if (result.ok) {
        ElMessage.success(`${device.serial} 已解除锁定`)
      } else {
        ElMessage.error(result.error || '操作失败')
      }
      return
    }
    if (!currentUser) {
      ElMessage.warning('无法获取当前用户信息，请重新登录')
      return
    }
    const result = await store.doLock(device.serial, currentUser, 3600, 'user')
    if (result.ok) {
      ElMessage.success(`已锁定 ${device.serial}`)
    } else {
      ElMessage.error(result.error || '锁定失败')
    }
  }

  // ── Queue ──
  async function handleJoinQueue(device) {
    if (!currentUser) {
      ElMessage.warning('无法获取当前用户信息，请重新登录')
      return
    }
    const result = await store.doJoinQueue(device.serial, currentUser)
    if (result.ok) {
      const pos = result.position || '?'
      ElMessage.success(`已加入 ${device.serial} 的等待队列，当前位置：第 ${pos} 位`)
    } else {
      ElMessage.error(result.error || '加入队列失败')
    }
  }

  async function handleCancelQueue(serial, uid) {
    await store.doLeaveQueue(serial, uid)
    await store.fetchQueue()
  }

  // ── Occupy / Release ──
  function handleOccupyClick(device) {
    if (device.occupied_by) {
      handleRelease(device.serial)
    }
  }

  async function handleRelease(serial) {
    const dev = store.devices.find((d) => d.serial === serial)
    if (!dev) return

    const occupiedBy = dev.occupied_by || ''
    const isRunnerOccupied = RUNNER_OCCUPIED_PREFIXES.some(p => occupiedBy.startsWith(p))

    if (isRunnerOccupied) {
      ElMessage.error('设备正在执行用例，无法解除占用。请等待用例执行完毕。')
      return
    }

    const result = await store.doRelease(serial, {
      userId: currentUser, reason: 'manual',
    })
    if (result.ok) {
      ElMessage.success(`${serial} 已解除占用`)
    } else {
      ElMessage.error(result.error || '解除失败')
    }
  }

  // ── Disconnect ──
  function openDisconnectDialog(serial) {
    const dev = store.devices.find((d) => d.serial === serial)
    if (!dev) return
    const isBusyOthers =
      dev.status === 'BUSY' && dev.locked_by && dev.locked_by !== currentUser
    disconnectDialog.value = {
      visible: true, serial,
      model: dev.model || dev.name || '',
      status: dev.status,
      lockedBy: dev.locked_by || '',
      isBusyOthers,
    }
  }

  async function handleDisconnectConfirm({ reason }) {
    const { serial, isBusyOthers } = disconnectDialog.value
    const result = await store.doDisconnect(serial, {
      force: isBusyOthers, reason, userId: currentUser, isAdmin: isBusyOthers,
    })
    if (result.ok) {
      ElMessage.success(`${serial} 已断开`)
      disconnectDialog.value.visible = false
    } else {
      ElMessage.error(result.error || '断开失败')
    }
  }

  function cancelDisconnectDialog() {
    disconnectDialog.value.visible = false
  }

  return {
    // dialog state
    disconnectDialog,
    networkDialog,
    // current user
    currentUser,
    // lifecycle
    loadDevices,
    startHeartbeat,
    stopHeartbeat,
    // actions
    handleRefresh,
    openNetworkDialog,
    handleNetworkConnect,
    cancelNetworkDialog,
    handleRowClick,
    handleLockClick,
    handleJoinQueue,
    handleCancelQueue,
    handleOccupyClick,
    handleRelease,
    openDisconnectDialog,
    handleDisconnectConfirm,
    cancelDisconnectDialog,
  }
}
