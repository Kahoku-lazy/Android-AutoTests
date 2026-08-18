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
  apiHeartbeat,
} from '../api'
import type {
  DeviceRecord,
  ScanResponse,
  DeviceOpResponse,
} from '@/shared/types/device'

// ── 返回类型接口 ──

export interface UseDevicePoolStateReturn {
  // state
  devices: Ref<DeviceRecord[]>
  currentSerial: Ref<string>
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
  doConnect: (serial: string, opts?: { activate?: boolean }) => Promise<DeviceOpResponse>
  doActivate: (serial: string) => Promise<DeviceOpResponse>
  doLock: (serial: string, locked: boolean) => Promise<DeviceOpResponse>
  doRelease: (serial: string) => Promise<DeviceOpResponse>
  doDisconnect: (serial: string) => Promise<DeviceOpResponse>
  doHeartbeat: () => Promise<void>
  selectDevice: (serial: string) => void
}

// ── Composable ──

export function useDevicePoolState(): UseDevicePoolStateReturn {
  // ── State ──
  const devices = ref<DeviceRecord[]>([])
  const currentSerial = ref('')
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
      if (data.status && data.data) {
        devices.value = data.data.devices || []
        currentSerial.value = data.data.current || ''
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
        devices.value = data.data?.devices || []
        if (data.data?.devices?.length && !currentSerial.value) {
          currentSerial.value = data.data.devices[0].serial
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

  async function doConnect(serial: string, opts: { activate?: boolean } = {}): Promise<DeviceOpResponse> {
    try {
      const { data } = await apiConnectDevice(serial, opts)
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

  async function doLock(serial: string, locked: boolean): Promise<DeviceOpResponse> {
    try {
      const { data } = await apiLockDevice(serial, locked)
      if (data.status) {
        await fetchDevices()
      }
      return data
    } catch (e: unknown) {
      const errData = (e as { response?: { data?: DeviceOpResponse } })?.response?.data
      return errData || { status: false, message: '操作失败' }
    }
  }

  async function doRelease(serial: string): Promise<DeviceOpResponse> {
    try {
      const { data } = await apiReleaseDevice(serial)
      if (data.status) {
        await fetchDevices()
      }
      return data
    } catch (e: unknown) {
      console.error('[device-pool] doRelease failed:', e)
      return { status: false, message: '释放失败' }
    }
  }

  async function doDisconnect(serial: string): Promise<DeviceOpResponse> {
    try {
      const { data } = await apiDisconnect(serial)
      if (data.status) {
        await fetchDevices()
      }
      return data
    } catch (e: unknown) {
      const errData = (e as { response?: { data?: DeviceOpResponse } })?.response?.data
      return errData || { status: false, message: '删除失败' }
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
    doHeartbeat,
    selectDevice,
  }
}
