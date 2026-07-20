<script setup>
/** DeviceSelector — 设备选择下拉框 + 手动连接/断开 + 当前设备信息栏

  Obser mode: 用户主动选择设备 → 点击"连接" → 使用 → 离开页面自动断开。
  已占用的设备（执行引擎运行中）不显示在下拉列表中。
*/
import { ref } from 'vue'
import { useElementStore } from '../store.js'

const store = useElementStore()
const refreshing = ref(false)
const pendingSerial = ref('')   // selected but not yet connected

const statusText = (status) => status === 'BUSY' ? '使用中' : '在线'
const statusTagType = (status) => status === 'BUSY' ? 'warning' : 'success'

function onDropdownChange(serial) {
  pendingSerial.value = serial
}

async function handleConnect() {
  const serial = pendingSerial.value || store.currentSerial
  if (!serial) return
  await store.connectDevice(serial)
  pendingSerial.value = ''
}

function handleDisconnect() {
  store.disconnectDevice()
  pendingSerial.value = ''
}

async function refreshDevices() {
  refreshing.value = true
  await store.fetchDevices()
  refreshing.value = false
}
</script>

<template>
  <div class="device-selector">
    <!-- Device dropdown — filtered to available (non-occupied) devices -->
    <el-select
      :model-value="store.isConnected ? store.connectedSerial : pendingSerial"
      placeholder="选择设备"
      size="default"
      style="width:260px"
      @change="onDropdownChange"
      :disabled="store.isConnected"
    >
      <el-option-group v-if="store.availableDevices.length" label="可用设备">
        <el-option
          v-for="d in store.availableDevices"
          :key="d.serial"
          :label="`${d.brand || ''} ${d.model || d.serial}`"
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

    <!-- Connect / Disconnect buttons -->
    <el-button
      v-if="!store.isConnected"
      type="primary"
      size="small"
      :disabled="!pendingSerial"
      @click="handleConnect"
    >
      连接
    </el-button>
    <el-button type="primary"
      v-else
      
      size="small"
      plain
      @click="handleDisconnect"
     danger>
      断开
    </el-button>

    <!-- Current device indicator -->
    <div v-if="store.isConnected && store.currentDevice" class="current-info">
      <el-tag type="success" size="small" effect="dark">已连接</el-tag>
      <span class="dev-label">
        {{ store.currentDevice.brand }} {{ store.currentDevice.model || store.currentSerial }}
      </span>
      <span class="dev-res">{{ store.currentDevice.screen_w }}×{{ store.currentDevice.screen_h }}</span>
      <el-tag size="small" effect="plain" type="info">
        {{ store.currentDevice.connection_type === 'WIFI' ? '📶 WiFi' : '🔌 USB' }}
      </el-tag>
    </div>
    <div v-else-if="!store.isConnected" class="current-info no-device">
      <span>未连接设备 — 请选择设备并点击"连接"</span>
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
  flex-wrap: wrap;
}
.current-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-secondary);
}
.current-info.no-device {
  color: var(--el-color-warning);
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
