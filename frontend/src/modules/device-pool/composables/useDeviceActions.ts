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
  handleNetworkConnect: (opts: { target: string; pair_port?: string; pair_code?: string }) => Promise<void>
  cancelNetworkDialog: () => void
  handleRowClick: (record: DeviceRecord) => void
  handleLockClick: (device: DeviceRecord) => Promise<void>
  handleRelease: (serial: string) => Promise<void>
  openDisconnectDialog: (serial: string) => void
  handleDisconnectConfirm: () => Promise<void>
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
      ElMessage.success(`扫描完成，发现 ${result.data?.count || 0} 台设备`)
    } else if (result && !result.status) {
      ElMessage.error(result.message || '扫描失败')
    }
    await loadDevices()
  }

  // ── Network (LAN) connect ──
  function openNetworkDialog() {
    networkDialog.value = { visible: true, loading: false }
  }

  async function handleNetworkConnect(opts: {
    target: string
    pair_port?: string
    pair_code?: string
  }) {
    if (!opts.target) return
    networkDialog.value.loading = true
    const extra =
      opts.pair_port && opts.pair_code
        ? { pair_port: opts.pair_port, pair_code: opts.pair_code }
        : undefined
    const result = await pool.doScan(opts.target, extra)
    networkDialog.value.loading = false
    if (result && result.status) {
      ElMessage.success(`已连接 ${opts.target}`)
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
    if (record.status !== 'ONLINE' && record.status !== 'BUSY') return
    pool.selectDevice(record.serial)
  }

  // ── 锁定 / 公开切换 ──
  async function handleLockClick(device: DeviceRecord) {
    const nextLocked = !device.locked
    const result = await pool.doLock(device.serial, nextLocked)
    if (result.status) {
      ElMessage.success(nextLocked ? `已锁定 ${device.serial}` : `${device.serial} 已公开`)
    } else {
      ElMessage.error(result.message || '操作失败')
    }
  }

  // ── 强制释放 ──
  async function handleRelease(serial: string) {
    const result = await pool.doRelease(serial)
    if (result.status) {
      ElMessage.success(`${serial} 已解除占用`)
    } else {
      ElMessage.error(result.message || '释放失败')
    }
  }

  // ── 删除 ──
  function openDisconnectDialog(serial: string) {
    const dev = pool.devices.value.find((d) => d.serial === serial)
    if (!dev) return
    disconnectDialog.value = {
      visible: true,
      serial,
      model: dev.model || dev.name || '',
      status: dev.status,
      lockedBy: dev.locked_by || '',
      isBusyOthers: false,
    }
  }

  async function handleDisconnectConfirm() {
    const { serial } = disconnectDialog.value
    const result = await pool.doDisconnect(serial)
    if (result.status) {
      ElMessage.success(`${serial} 已删除`)
      disconnectDialog.value.visible = false
    } else {
      ElMessage.error(result.message || '删除失败')
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
    handleRelease,
    openDisconnectDialog,
    handleDisconnectConfirm,
    cancelDisconnectDialog,
  }
}
