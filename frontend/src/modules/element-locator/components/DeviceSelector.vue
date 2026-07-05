<script setup>
/** DeviceSelector — 设备选择下拉框 + 当前设备信息栏 */
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useElementStore } from '../store.js'

const store = useElementStore()
const refreshing = ref(false)

const selectedSerial = computed({
  get: () => store.currentSerial,
  set: (val) => { /* handled by @change */ },
})

const statusText = (status) => status === 'BUSY' ? '使用中' : '在线'
const statusTagType = (status) => status === 'BUSY' ? 'warning' : 'success'

function deviceLabel(d) {
  const parts = []
  if (d.brand) parts.push(d.brand)
  if (d.model) parts.push(d.model)
  if (!parts.length) parts.push(d.serial)
  if (d.screen) parts.push(`(${d.screen})`)
  return parts.join(' ')
}

async function onDeviceSelect(serial) {
  if (!serial || serial === store.currentSerial) return
  await store.activateDevice(serial)
}

async function refreshDevices() {
  refreshing.value = true
  await store.fetchDevices()
  refreshing.value = false
}
</script>

<template>
  <div class="device-selector">
    <!-- Device dropdown -->
    <el-select
      :model-value="store.currentSerial"
      placeholder="选择设备"
      size="default"
      style="width:260px"
      @change="onDeviceSelect"
      :disabled="!store.hasDevices"
    >
      <el-option-group v-if="store.onlineDevices.length" label="可用设备">
        <el-option
          v-for="d in store.onlineDevices"
          :key="d.serial"
          :label="deviceLabel(d)"
          :value="d.serial"
        >
          <div class="opt-row">
            <span class="opt-model">{{ d.brand }} {{ d.model || d.serial }}</span>
            <el-tag :type="statusTagType(d.status)" size="small" effect="plain">
              {{ statusText(d.status) }}
            </el-tag>
          </div>
          <div class="opt-sub">
            <span class="opt-serial">{{ d.serial }}</span>
            <span v-if="d.screen" class="opt-screen">{{ d.screen }}</span>
            <span v-if="d.connection_type" class="opt-conn">{{ d.connection_type === 'WIFI' ? '📶' : '🔌' }}</span>
          </div>
        </el-option>
      </el-option-group>
      <template v-if="!store.hasDevices" #empty>
        <div class="no-devices-empty">
          <p>无可用设备</p>
          <p class="hint">请先在「设备管理」中连接设备</p>
        </div>
      </template>
    </el-select>

    <!-- Current device indicator -->
    <div v-if="store.currentDevice" class="current-info">
      <span class="dev-label">
        {{ store.currentDevice.brand }} {{ store.currentDevice.model || store.currentSerial }}
      </span>
      <span class="dev-res">{{ store.currentDevice.screen_w }}×{{ store.currentDevice.screen_h }}</span>
      <el-tag size="small" effect="plain" type="info">
        {{ store.currentDevice.connection_type === 'WIFI' ? '📶 WiFi' : '🔌 USB' }}
      </el-tag>
    </div>
    <div v-else class="current-info no-device">
      <span>未连接设备</span>
    </div>

    <!-- Refresh -->
    <el-button :icon="'Refresh'" circle size="small" @click="refreshDevices" :loading="refreshing" />
  </div>
</template>

<style scoped>
.device-selector {
  display: flex;
  align-items: center;
  gap: 12px;
}
.current-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-secondary);
}
.current-info.no-device {
  color: var(--el-color-danger);
}
.dev-label {
  font-weight: 600;
  color: var(--text-primary);
}
.dev-res {
  font-family: monospace;
  background: var(--el-fill-color-light);
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 12px;
}
.opt-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.opt-model {
  font-weight: 500;
}
.opt-sub {
  display: flex;
  gap: 8px;
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}
.opt-serial {
  font-family: monospace;
  font-size: 11px;
}
.no-devices-empty {
  text-align: center;
  padding: 12px 0;
}
.no-devices-empty .hint {
  font-size: 12px;
  color: var(--text-secondary);
}
</style>
