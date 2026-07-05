/** element-locator Pinia store — device + element state */
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'
import {
  apiDump, apiAction,
  apiGetDevices, apiActivateDevice, apiGetDeviceInfo,
} from './api.js'

export const useElementStore = defineStore('element-locator', () => {
  // ── Device state ──
  const devices = ref([])
  const currentSerial = ref('')
  const currentDevice = ref(null)   // { serial, model, brand, screen_w, screen_h, connection_type, package }
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
  const lastDump = ref(null)        // last dump response

  // ── Computed ──
  const onlineDevices = computed(() =>
    devices.value.filter(d => d.status === 'ONLINE' || d.status === 'BUSY')
  )
  const hasDevices = computed(() => onlineDevices.value.length > 0)
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
        if (data.current) {
          currentSerial.value = data.current
        }
        if (currentSerial.value) {
          const cd = devices.value.find(d => d.serial === currentSerial.value)
          if (cd) {
            currentDevice.value = {
              serial: cd.serial,
              model: cd.model,
              brand: cd.brand,
              screen_w: cd.screen_w || (cd.screen ? parseInt(cd.screen.split('x')[0]) : 0),
              screen_h: cd.screen_h || (cd.screen ? parseInt(cd.screen.split('x')[1]) : 0),
              connection_type: cd.connection_type,
              status: cd.status,
            }
            if (currentDevice.value.screen_w) screenW.value = currentDevice.value.screen_w
            if (currentDevice.value.screen_h) screenH.value = currentDevice.value.screen_h
          }
        } else if (onlineDevices.value.length) {
          await activateDevice(onlineDevices.value[0].serial, { silent: true })
        }
      }
    } catch (_) { /* silent */ }
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
        if (actionable.value.length) {
          actionable.value.forEach((e, i) => {
            e._idx = i
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
    devices, currentSerial, currentDevice, screenW, screenH, wsConnected,
    onlineDevices, hasDevices, isDeviceOnline,
    // element state
    elements, actionable, selected, pageId, loading, error, lastDump,
    // device actions
    fetchDevices, activateDevice, fetchCurrentDevice,
    // element actions
    doDump, doAction, selectElement, clearError,
  }
})
