/** element-locator Pinia store — device + element state

  Device connection is now manual (observe mode):
  - User selects a device and clicks "Connect" to observe it
  - Occupied devices are filtered from the dropdown
  - Leaving the page auto-disconnects
*/
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'
import {
  apiDump, apiAction,
  apiGetDevices, apiActivateDevice, apiGetDeviceInfo,
  apiConnectObserve, apiDisconnectObserve,
} from './api.js'

// Process prefixes that indicate execution engine occupation — these devices
// are unavailable for element-locator and case-manager
const EXEC_PREFIXES = ['runner-', 'ai_agent', 'task-', 'run-']

function isExecutionOccupied(device) {
  return device.status === 'BUSY' && device.occupied_by &&
    EXEC_PREFIXES.some(p => device.occupied_by.startsWith(p))
}

export const useElementStore = defineStore('element-locator', () => {
  // ── Device state ──
  const devices = ref([])
  const currentSerial = ref('')
  const connectedSerial = ref('')   // explicitly connected (observe mode)
  const currentDevice = ref(null)
  const screenW = ref(1440)
  const screenH = ref(3040)
  const wsConnected = ref(false)

  // ── Element state ──
  const elements = ref([])
  const actionable = ref([])
  const selected = ref(null)
  const pageId = ref(null)
  const loading = ref(false)
  const error = ref('')
  const lastDump = ref(null)
  const screenshotUrl = ref('')   // shared screenshot for thumbnail cropping

  // ── Computed ──
  const onlineDevices = computed(() =>
    devices.value.filter(d => d.status === 'ONLINE' || d.status === 'BUSY')
  )
  /** Devices available for observe connection (excludes execution-occupied) */
  const availableDevices = computed(() =>
    onlineDevices.value.filter(d => !isExecutionOccupied(d))
  )
  const hasDevices = computed(() => availableDevices.value.length > 0)
  const isConnected = computed(() => !!connectedSerial.value)
  const isDeviceOnline = computed(() => {
    const d = devices.value.find(d => d.serial === currentSerial.value)
    return d && (d.status === 'ONLINE' || d.status === 'BUSY')
  })

  // ── Device actions ──

  async function fetchDevices() {
    try {
      const { data } = await apiGetDevices()
      if (data.ok) {
        devices.value = data.devices || []
        // Restore current device info if still connected
        if (connectedSerial.value) {
          const cd = devices.value.find(d => d.serial === connectedSerial.value)
          if (cd) {
            currentSerial.value = cd.serial
            currentDevice.value = {
              serial: cd.serial, model: cd.model, brand: cd.brand,
              screen_w: cd.screen_w || 0,
              screen_h: cd.screen_h || 0,
              connection_type: cd.connection_type,
              status: cd.status,
            }
            if (currentDevice.value.screen_w) screenW.value = currentDevice.value.screen_w
            if (currentDevice.value.screen_h) screenH.value = currentDevice.value.screen_h
          } else {
            // Connected device went offline — clear connection
            disconnectDevice()
          }
        }
        // NOTE: No auto-select — user must explicitly connect
      }
    } catch (_) { /* silent */ }
  }

  /** Connect to a device in observe mode (lightweight, no lock) */
  async function connectDevice(serial) {
    try {
      const { data } = await apiConnectObserve(serial)
      if (data.ok) {
        connectedSerial.value = serial
        currentSerial.value = serial
        await fetchCurrentDevice()
        ElMessage.success(`已连接设备 ${serial}`)
        return true
      }
      ElMessage.error(data.error || '连接设备失败')
      return false
    } catch (_) {
      ElMessage.error('连接设备失败')
      return false
    }
  }

  /** Disconnect from the currently observed device */
  function disconnectDevice() {
    const serial = connectedSerial.value
    if (!serial) return
    apiDisconnectObserve(serial).catch(() => {})
    connectedSerial.value = ''
    currentSerial.value = ''
    currentDevice.value = null
    // Reset element state
    elements.value = []
    actionable.value = []
    pageId.value = null
    selected.value = null
  }

  async function activateDevice(serial, { silent = false } = {}) {
    try {
      const { data } = await apiActivateDevice(serial)
      if (data.ok) {
        currentSerial.value = serial
        await fetchCurrentDevice()
        if (!silent) ElMessage.success(`已切换到 ${serial}`)
        return data
      }
      if (!silent) ElMessage.error(data.error || '切换设备失败')
      return data
    } catch (_) {
      if (!silent) ElMessage.error('切换设备失败')
      return { ok: false }
    }
  }

  async function fetchCurrentDevice() {
    try {
      const { data } = await apiGetDeviceInfo()
      if (data.ok) {
        currentDevice.value = {
          serial: data.serial,
          model: data.model || '',
          brand: data.brand || '',
          screen_w: data.screen_w || 1440,
          screen_h: data.screen_h || 3040,
          connection_type: data.connection_type || 'USB',
          package: data.package || '',
        }
        screenW.value = data.screen_w || 1440
        screenH.value = data.screen_h || 3040
        currentSerial.value = data.serial
        return data
      }
    } catch (_) { /* silent */ }
    return null
  }

  // ── Element actions ──

  async function doDump() {
    loading.value = true
    error.value = ''
    try {
      const { data } = await apiDump()
      if (data.ok) {
        elements.value = data.elements || []
        actionable.value = data.actionable || []
        pageId.value = data.page_id
        lastDump.value = data
        // Update device serial from response
        if (data.serial) currentSerial.value = data.serial
        if (elements.value.length) {
          elements.value.forEach((e, i) => {
            e._idx = i
          })
        }
        if (actionable.value.length) {
          // Sync _idx with elements so selection works across both arrays
          const idxMap = new Map()
          elements.value.forEach(e => {
            idxMap.set((e.bounds || '') + '|' + (e.class_name || ''), e._idx)
          })
          actionable.value.forEach((e) => {
            const key = (e.bounds || '') + '|' + (e.class_name || '')
            e._idx = idxMap.has(key) ? idxMap.get(key) : e._idx
          })
        }
        return data
      } else {
        error.value = data.error || 'Dump failed'
      }
    } catch (e) {
      error.value = e.message || 'Dump failed'
    } finally {
      loading.value = false
    }
    return null
  }

  async function doAction(action, x, y) {
    try {
      const { data } = await apiAction(action, x, y)
      if (!data.ok) {
        error.value = data.error || 'Action failed'
        return false
      }
      return true
    } catch (e) {
      error.value = e.message || 'Action failed'
      return false
    }
  }

  function selectElement(el) {
    selected.value = el
  }

  function clearError() {
    error.value = ''
  }

  return {
    // device state
    devices, currentSerial, connectedSerial, currentDevice, screenW, screenH, wsConnected,
    onlineDevices, availableDevices, hasDevices, isConnected, isDeviceOnline,
    // element state
    elements, actionable, selected, pageId, loading, error, lastDump, screenshotUrl,
    // device actions
    fetchDevices, connectDevice, disconnectDevice, activateDevice, fetchCurrentDevice,
    // element actions
    doDump, doAction, selectElement, clearError,
  }
})
