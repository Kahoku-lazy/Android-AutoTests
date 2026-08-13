/** useDevicePoolState — 设备池状态管理 composable（替代 Pinia store） */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import {
  apiListDevices,
  apiScanDevices,
  apiConnectDevice,
  apiActivate,
  apiLockDevice,
  apiReleaseDevice,
  apiDisconnect,
  apiGetQueue,
  apiJoinQueue,
  apiLeaveQueue,
  apiHeartbeat,
} from '../api'
import type {
  DeviceRecord,
  QueueEntry,
  ScanResponse,
  DeviceOpResponse,
} from '@/shared/types/device'

// ── 返回类型接口 ──

export interface UseDevicePoolStateReturn {
  // state
  devices: Ref<DeviceRecord[]>
  currentSerial: Ref<string>
  queueLength: Ref<number>
  queueEntries: Ref<QueueEntry[]>
  loading: Ref<boolean>
  selectedSerial: Ref<string | null>
  scanning: Ref<boolean>
  error: Ref<string | null>
  // getters
  selectedDevice: ComputedRef<DeviceRecord | undefined>
  onlineDevices: ComputedRef<DeviceRecord[]>
  hasDevices: ComputedRef<boolean>
  // actions
  fetchDevices: () => Promise<void>
  doScan: (target?: string) => Promise<ScanResponse>
  doConnect: (serial: string, opts?: Record<string, unknown>) => Promise<DeviceOpResponse>
  doActivate: (serial: string) => Promise<DeviceOpResponse>
  doLock: (serial: string, userId: string, timeout?: number, type?: string) => Promise<DeviceOpResponse>
  doRelease: (serial: string, opts?: Record<string, unknown>) => Promise<DeviceOpResponse>
  doDisconnect: (serial: string, opts?: Record<string, unknown>) => Promise<DeviceOpResponse>
  fetchQueue: () => Promise<void>
  doJoinQueue: (serial: string, userId: string) => Promise<DeviceOpResponse & { position?: number }>
  doLeaveQueue: (serial: string, userId: string) => Promise<DeviceOpResponse>
  doHeartbeat: () => Promise<void>
  selectDevice: (serial: string) => void
}

// ── Composable ──

export function useDevicePoolState(): UseDevicePoolStateReturn {
  // ── State ──
  const devices = ref<DeviceRecord[]>([])
  const currentSerial = ref('')
  const queueLength = ref(0)
  const queueEntries = ref<QueueEntry[]>([])
  const loading = ref(false)
  const selectedSerial = ref<string | null>(null)
  const scanning = ref(false)
  const error = ref<string | null>(null)

  // ── Getters ──
  const selectedDevice = computed(() =>
    devices.value.find((d) => d.serial === selectedSerial.value),
  )
  const onlineDevices = computed(() =>
    devices.value.filter((d) => d.status === 'ONLINE'),
  )
  const hasDevices = computed(() => devices.value.length > 0)

  // ── Actions ──

  async function fetchDevices() {
    loading.value = true
    error.value = null
    try {
      const { data } = await apiListDevices()
      if (data.status) {
        devices.value = (data.devices as DeviceRecord[]) || []
        currentSerial.value = (data.current as string) || ''
        queueLength.value = (data.queue_length as number) || 0
      }
    } catch (e: unknown) {
      error.value = '设备列表加载失败，请稍后重试'
      console.warn('[device-pool] fetchDevices failed:', (e as { message?: string })?.message || e)
    }
    loading.value = false
  }

  async function doScan(target?: string): Promise<ScanResponse> {
    scanning.value = true
    try {
      const { data } = await apiScanDevices(target)
      if (data.status) {
        devices.value = (data.devices as DeviceRecord[]) || []
        if (data.devices?.length && !currentSerial.value) {
          currentSerial.value = data.devices[0].serial
        }
        return data
      }
      return data
    } catch (e: unknown) {
      const errData = (e as { response?: { data?: ScanResponse } })?.response?.data
      return errData || { status: false, message: '扫描失败' }
    } finally {
      scanning.value = false
    }
  }

  async function doConnect(serial: string, opts: Record<string, unknown> = {}): Promise<DeviceOpResponse> {
    try {
      const { data } = await apiConnectDevice(serial, opts as Parameters<typeof apiConnectDevice>[1])
      if (data.status) {
        await fetchDevices()
      }
      return data
    } catch (e: unknown) {
      const errData = (e as { response?: { data?: DeviceOpResponse } })?.response?.data
      return errData || { status: false, message: '连接失败' }
    }
  }

  async function doActivate(serial: string): Promise<DeviceOpResponse> {
    try {
      const { data } = await apiActivate(serial)
      if (data.status) {
        currentSerial.value = serial
        await fetchDevices()
      }
      return data
    } catch (e: unknown) {
      console.error('[device-pool] doActivate failed:', e)
      return { status: false, message: '激活失败' }
    }
  }

  async function doLock(serial: string, userId: string, timeout = 300, type = 'user'): Promise<DeviceOpResponse> {
    try {
      const { data } = await apiLockDevice(serial, userId, timeout, type)
      if (data.status) {
        await fetchDevices()
      }
      return data
    } catch (e: unknown) {
      const errData = (e as { response?: { data?: DeviceOpResponse } })?.response?.data
      return errData || { status: false, message: '锁定失败' }
    }
  }

  async function doRelease(serial: string, opts: Record<string, unknown> = {}): Promise<DeviceOpResponse> {
    try {
      const { data } = await apiReleaseDevice(serial, opts as Parameters<typeof apiReleaseDevice>[1])
      if (data.status) {
        await fetchDevices()
      }
      return data
    } catch (e: unknown) {
      console.error('[device-pool] doRelease failed:', e)
      return { status: false, message: '释放失败' }
    }
  }

  async function doDisconnect(serial: string, opts: Record<string, unknown> = {}): Promise<DeviceOpResponse> {
    try {
      const { data } = await apiDisconnect(serial, opts as Parameters<typeof apiDisconnect>[1])
      if (data.status) {
        await fetchDevices()
      }
      return data
    } catch (e: unknown) {
      const errData = (e as { response?: { data?: DeviceOpResponse } })?.response?.data
      return errData || { status: false, message: '断开失败' }
    }
  }

  async function fetchQueue() {
    try {
      const { data } = await apiGetQueue()
      if (data.status) {
        queueEntries.value = (data.queue as QueueEntry[]) || []
        queueLength.value = (data.count as number) || 0
      }
    } catch (e: unknown) {
      console.error('[device-pool] fetchQueue failed:', (e as { message?: string })?.message || e)
    }
  }

  async function doJoinQueue(serial: string, userId: string): Promise<DeviceOpResponse & { position?: number }> {
    try {
      const { data } = await apiJoinQueue(serial, userId)
      if (data.status) {
        await fetchQueue()
      }
      return data
    } catch (e: unknown) {
      console.error('[device-pool] doJoinQueue failed:', e)
      return { status: false, message: '加入排队失败' }
    }
  }

  async function doLeaveQueue(serial: string, userId: string): Promise<DeviceOpResponse> {
    try {
      const { data } = await apiLeaveQueue(serial, userId)
      if (data.status) {
        await fetchQueue()
      }
      return data
    } catch (e: unknown) {
      console.error('[device-pool] doLeaveQueue failed:', e)
      return { status: false, message: '取消排队失败' }
    }
  }

  async function doHeartbeat() {
    try {
      await apiHeartbeat()
    } catch (e: unknown) {
      console.debug('[device-pool] heartbeat:', (e as { message?: string })?.message || e)
    }
  }

  function selectDevice(serial: string) {
    selectedSerial.value = serial
  }

  return {
    devices,
    currentSerial,
    queueLength,
    queueEntries,
    loading,
    selectedSerial,
    scanning,
    error,
    selectedDevice,
    onlineDevices,
    hasDevices,
    fetchDevices,
    doScan,
    doConnect,
    doActivate,
    doLock,
    doRelease,
    doDisconnect,
    fetchQueue,
    doJoinQueue,
    doLeaveQueue,
    doHeartbeat,
    selectDevice,
  }
}
