/** device-inspector Pinia store — device + element state

  Device connection is manual (observe mode):
  - User selects a device and clicks "Connect" to observe it
  - Occupied devices are filtered from the dropdown
  - Leaving the page auto-disconnects
*/
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'
import {
  apiDump, apiOcr,
  apiGetDevices, apiActivateDevice, apiGetDeviceInfo,
  apiConnectObserve, apiDisconnectObserve,
} from './api'

// Process prefixes that indicate execution engine occupation — these devices
// are unavailable for inspector and case-manager
const EXEC_PREFIXES = ['runner-', 'ai_agent', 'task-', 'run-']

function isExecutionOccupied(device) {
  return device.status === 'BUSY' && device.occupied_by &&
    EXEC_PREFIXES.some(p => device.occupied_by.startsWith(p))
}

// Input widget class keywords for the "输入框" filter
const INPUT_CLASS_KEYWORDS = ['edittext', 'autocomplete', 'searchview']

function isInputClass(className) {
  if (!className) return false
  const c = className.toLowerCase()
  return INPUT_CLASS_KEYWORDS.some(k => c.includes(k))
}

export const useElementStore = defineStore('device-inspector', () => {
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
  const loading = ref(false)
  const error = ref('')
  const lastDump = ref(null)
  const screenshotUrl = ref('')   // shared screenshot for thumbnail cropping

  // ── OCR state ──
  const ocrResults = ref([])
  const ocrLoading = ref(false)
  const selectedOcr = ref(null)
  const activePanelTab = ref('elements')   // 'elements' | 'ocr'

  // ── Filter state ──
  const filterMode = ref('all')
  const searchText = ref('')

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
  /** Full element list filtered by mode + search text (page element list). */
  const filteredElements = computed(() => {
    let els = elements.value || []
    switch (filterMode.value) {
      case 'clickable': els = els.filter(e => e.clickable); break
      case 'text': els = els.filter(e => e.text); break
      case 'rid': els = els.filter(e => e.resource_id); break
      case 'clickable_text': els = els.filter(e => e.clickable && e.text); break
      case 'clickable_no_text': els = els.filter(e => e.clickable && !e.text); break
      case 'input': els = els.filter(e => isInputClass(e.class_name)); break
      case 'scrollable': els = els.filter(e => e.scrollable); break
    }
    const q = searchText.value.trim().toLowerCase()
    if (q) {
      els = els.filter(e =>
        (e.text || '').toLowerCase().includes(q) ||
        (e.resource_id || '').toLowerCase().includes(q) ||
        (e.content_desc || '').toLowerCase().includes(q) ||
        (e.class_name || '').toLowerCase().includes(q)
      )
    }
    return els
  })

  // ── Device actions ──

  async function fetchDevices() {
    try {
      const { data } = await apiGetDevices()
      if (data.status) {
        devices.value = data.data?.devices || []
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
    } catch (e) { console.error(e); }
  }

  /** Connect to a device in observe mode (lightweight, no lock) */
  async function connectDevice(serial) {
    try {
      const { data } = await apiConnectObserve(serial)
      if (data.status) {
        connectedSerial.value = serial
        currentSerial.value = serial
        await fetchCurrentDevice()
        ElMessage.success(`已连接设备 ${serial}`)
        return true
      }
      ElMessage.error(data.message || '连接设备失败')
      return false
    } catch (e) {
      ElMessage.error('连接设备失败')
      return false
      console.error(e);
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
    selected.value = null
  }

  async function activateDevice(serial, { silent = false } = {}) {
    try {
      const { data } = await apiActivateDevice(serial)
      if (data.status) {
        currentSerial.value = serial
        await fetchCurrentDevice()
        if (!silent) ElMessage.success(`已切换到 ${serial}`)
        return data
      }
      if (!silent) ElMessage.error(data.message || '切换设备失败')
      return data
    } catch (e) {
      if (!silent) ElMessage.error('切换设备失败')
      return { ok: false }
      console.error(e);
    }
  }

  async function fetchCurrentDevice() {
    try {
      const { data } = await apiGetDeviceInfo()
      if (data.status) {
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
    } catch (e) { console.error(e); }
    return null
  }

  // ── Element actions ──

  async function doDump() {
    loading.value = true
    error.value = ''
    try {
      const { data } = await apiDump()
      if (data.status) {
        elements.value = data.elements || []
        actionable.value = data.actionable || []
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
        error.value = data.message || 'Dump failed'
      }
    } catch (e) {
      error.value = e.message || 'Dump failed'
    } finally {
      loading.value = false
    }
    return null
  }

  async function doOcr() {
    ocrLoading.value = true
    try {
      const { data } = await apiOcr()
      if (data.status) {
        ocrResults.value = data.texts || []
        activePanelTab.value = 'ocr'
        return data
      }
      ElMessage.warning(data.message || 'OCR 识别失败')
    } catch (e) {
      ElMessage.error('OCR 识别失败')
    } finally {
      ocrLoading.value = false
    }
    return null
  }

  function selectElement(el) {
    selected.value = el
    selectedOcr.value = null
  }

  function selectOcr(item) {
    selectedOcr.value = item
    selected.value = null
    activePanelTab.value = 'ocr'
  }

  function clearError() {
    error.value = ''
  }

  return {
    // device state
    devices, currentSerial, connectedSerial, currentDevice, screenW, screenH, wsConnected,
    onlineDevices, availableDevices, hasDevices, isConnected, isDeviceOnline,
    // element state
    elements, actionable, selected, loading, error, lastDump, screenshotUrl,
    filterMode, searchText, filteredElements,
    // ocr state
    ocrResults, ocrLoading, selectedOcr, activePanelTab,
    // device actions
    fetchDevices, connectDevice, disconnectDevice, activateDevice, fetchCurrentDevice,
    // element actions
    doDump, doOcr, selectElement, selectOcr, clearError,
  }
})
