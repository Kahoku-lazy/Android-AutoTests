/**
 * useDeviceActions — 设备操作逻辑提取
 *
 * 从 index.vue 提取所有设备操作 handler、数据加载和动画逻辑。
 * 依赖 useDevicePoolState composable（替代原 Pinia store）。
 */
import { ref, nextTick, type Ref } from 'vue'
import { animate, stagger } from 'animejs'
import { ElMessage } from 'element-plus'
import { getActive } from '@/shared/auth/token-storage'
import {
  RUNNER_OCCUPIED_PREFIXES,
  DEFAULT_DIALOGS,
  LIST_ANIMATION,
} from '../constants'
import type {
  DeviceRecord,
  DisconnectDialogState,
  NetworkDialogState,
} from '@/shared/types/device'
import type { UseDevicePoolStateReturn } from './useDevicePoolState'

// ── 返回类型接口 ──

export interface UseDeviceActionsReturn {
  disconnectDialog: Ref<DisconnectDialogState>
  networkDialog: Ref<NetworkDialogState>
  currentUser: string
  loadDevices: () => Promise<void>
  handleRefresh: () => Promise<void>
  openNetworkDialog: () => void
  handleNetworkConnect: (opts: { target: string }) => Promise<void>
  cancelNetworkDialog: () => void
  handleRowClick: (record: DeviceRecord) => void
  handleLockClick: (device: DeviceRecord) => Promise<void>
  handleJoinQueue: (device: DeviceRecord) => Promise<void>
  handleCancelQueue: (serial: string, uid: string) => Promise<void>
  handleOccupyClick: (device: DeviceRecord) => void
  handleRelease: (serial: string) => Promise<void>
  openDisconnectDialog: (serial: string) => void
  handleDisconnectConfirm: (opts: { reason: string }) => Promise<void>
  cancelDisconnectDialog: () => void
}

// ── Composable ──

export function useDeviceActions(pool: UseDevicePoolStateReturn): UseDeviceActionsReturn {
  // ── Dialog state ──
  const disconnectDialog = ref<DisconnectDialogState>({ ...DEFAULT_DIALOGS.disconnect })
  const networkDialog = ref<NetworkDialogState>({ ...DEFAULT_DIALOGS.network })

  // ── Internal state ──
  let prevDevicesJson = ''

  // ── Current user ──
  const currentUser = getActive()

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
    await pool.fetchDevices()
    await nextTick()
    const json = JSON.stringify(pool.devices.value)
    if (json !== prevDevicesJson) {
      prevDevicesJson = json
      animateDeviceRows()
    }
  }

  // ── Refresh / Scan ──
  async function handleRefresh() {
    if (pool.scanning.value || pool.loading.value) return
    const result = await pool.doScan()
    if (result && result.status) {
      ElMessage.success(`扫描完成，发现 ${(result as { count?: number }).count || 0} 台设备`)
    } else if (result && !result.status) {
      ElMessage.error(result.message || '扫描失败')
    }
    await loadDevices()
  }

  // ── Network (LAN) connect ──
  function openNetworkDialog() {
    networkDialog.value = { visible: true, loading: false }
  }

  async function handleNetworkConnect({ target }: { target: string }) {
    if (!target) return
    networkDialog.value.loading = true
    const result = await pool.doScan(target)
    networkDialog.value.loading = false
    if (result && result.status) {
      ElMessage.success(`已连接 ${target}`)
      networkDialog.value.visible = false
      await loadDevices()
    } else {
      ElMessage.error((result && result.message) || '连接失败')
    }
  }

  function cancelNetworkDialog() {
    networkDialog.value.visible = false
  }

  // ── Row click ──
  function handleRowClick(record: DeviceRecord) {
    if (!record || !record.serial) return
    const dev = pool.devices.value.find((d) => d.serial === record.serial)
    if (!dev) return
    if (dev.status === 'OFFLINE' || dev.status === 'DISCONNECTED') return
    pool.selectDevice(record.serial)
  }

  // ── Lock / Unlock ──
  async function handleLockClick(device: DeviceRecord) {
    if (device.locked_by) {
      if (device.locked_by !== currentUser) {
        ElMessage.warning(`设备已被 ${device.locked_by} 锁定，只有锁定者可以解除`)
        return
      }
      const result = await pool.doRelease(device.serial, {
        unlock: true, reason: 'manual', userId: currentUser,
      })
      if (result.status) {
        ElMessage.success(`${device.serial} 已解除锁定`)
      } else {
        ElMessage.error(result.message || '操作失败')
      }
      return
    }
    if (!currentUser) {
      ElMessage.warning('无法获取当前用户信息，请重新登录')
      return
    }
    const result = await pool.doLock(device.serial, currentUser, 3600, 'user')
    if (result.status) {
      ElMessage.success(`已锁定 ${device.serial}`)
    } else {
      ElMessage.error(result.message || '锁定失败')
    }
  }

  // ── Queue ──
  async function handleJoinQueue(device: DeviceRecord) {
    if (!currentUser) {
      ElMessage.warning('无法获取当前用户信息，请重新登录')
      return
    }
    const result = await pool.doJoinQueue(device.serial, currentUser)
    if (result.status) {
      const pos = (result as { position?: number }).position || '?'
      ElMessage.success(`已加入 ${device.serial} 的等待队列，当前位置：第 ${pos} 位`)
    } else {
      ElMessage.error(result.message || '加入队列失败')
    }
  }

  async function handleCancelQueue(serial: string, uid: string) {
    await pool.doLeaveQueue(serial, uid)
    await pool.fetchQueue()
  }

  // ── Occupy / Release ──
  function handleOccupyClick(device: DeviceRecord) {
    if (device.occupied_by) {
      handleRelease(device.serial)
    }
  }

  async function handleRelease(serial: string) {
    const dev = pool.devices.value.find((d) => d.serial === serial)
    if (!dev) return

    const occupiedBy = dev.occupied_by || ''
    const isRunnerOccupied = RUNNER_OCCUPIED_PREFIXES.some((p) => occupiedBy.startsWith(p))

    if (isRunnerOccupied) {
      ElMessage.error('设备正在执行用例，无法解除占用。请等待用例执行完毕。')
      return
    }

    const result = await pool.doRelease(serial, {
      userId: currentUser, reason: 'manual',
    })
    if (result.status) {
      ElMessage.success(`${serial} 已解除占用`)
    } else {
      ElMessage.error(result.message || '解除失败')
    }
  }

  // ── Disconnect ──
  function openDisconnectDialog(serial: string) {
    const dev = pool.devices.value.find((d) => d.serial === serial)
    if (!dev) return
    const isBusyOthers =
      dev.status === 'BUSY' && !!dev.locked_by && dev.locked_by !== currentUser
    disconnectDialog.value = {
      visible: true,
      serial,
      model: dev.model || dev.name || '',
      status: dev.status,
      lockedBy: dev.locked_by || '',
      isBusyOthers,
    }
  }

  async function handleDisconnectConfirm({ reason }: { reason: string }) {
    const { serial, isBusyOthers } = disconnectDialog.value
    const result = await pool.doDisconnect(serial, {
      force: isBusyOthers,
      reason,
      userId: currentUser,
      isAdmin: isBusyOthers,
    })
    if (result.status) {
      ElMessage.success(`${serial} 已断开`)
      disconnectDialog.value.visible = false
    } else {
      ElMessage.error(result.message || '断开失败')
    }
  }

  function cancelDisconnectDialog() {
    disconnectDialog.value.visible = false
  }

  return {
    disconnectDialog,
    networkDialog,
    currentUser,
    loadDevices,
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
