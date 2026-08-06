<script setup>
/** DeviceSelector — 设备选择下拉框 + 手动连接/断开 + 当前设备信息栏

  Obser mode: 用户主动选择设备 → 点击"连接" → 使用 → 离开页面自动断开。
  已占用的设备（执行引擎运行中）不显示在下拉列表中。
*/
import { ref } from 'vue'
import { useElementStore } from '../store'

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
  <div class="device-bar">
    <!-- Left: device select + connect -->
    <div class="device-bar__left">
      <el-select
        :model-value="store.isConnected ? store.connectedSerial : pendingSerial"
        placeholder="选择设备"
        size="default"
        class="device-select"
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
            </div>
          </el-option>
        </el-option-group>
      </el-select>

      <button v-if="!store.isConnected" class="dev-btn dev-btn--primary" :disabled="!pendingSerial" @click="handleConnect">连接</button>
      <button v-else class="dev-btn dev-btn--danger" @click="handleDisconnect">断开</button>
    </div>

    <!-- Center: current device info -->
    <div class="device-bar__info">
      <template v-if="store.isConnected && store.currentDevice">
        <span class="dev-dot dev-dot--live"></span>
        <span class="dev-name">{{ store.currentDevice.brand }} {{ store.currentDevice.model || store.currentSerial }}</span>
        <span class="dev-meta">· {{ store.currentDevice.screen_w }}×{{ store.currentDevice.screen_h }} · {{ store.currentDevice.connection_type === 'WIFI' ? 'WiFi' : 'USB' }}</span>
        <span class="dev-tag dev-tag--online">已连接</span>
      </template>
      <template v-else>
        <span class="dev-dot"></span>
        <span class="dev-meta">未连接设备 — 选择设备后点击连接</span>
      </template>
    </div>

    <!-- Right: refresh -->
    <button class="dev-btn" @click="refreshDevices" :disabled="refreshing">
      {{ refreshing ? '...' : '↻' }}
    </button>
  </div>
</template>

<style scoped>
/* Paper × Polaroid — 设备栏 */
.device-bar {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 10px 16px;
  background: #fff;
  border: 3px solid var(--app-ink, #2d2d2d);
  border-radius: 6px 10px 6px 10px;
  box-shadow: 2px 2px 0 rgba(0,0,0,0.04);
  flex-shrink: 0;
  flex-wrap: wrap;
}
.device-bar__left { display: flex; align-items: center; gap: 8px; }
.device-bar__info { display: flex; align-items: center; gap: 6px; flex: 1; min-width: 0; }
.device-select { width: 240px; }

.dev-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--app-ink-muted, #999); flex-shrink: 0; }
.dev-dot--live { background: var(--app-status-success, #6BCB77); }
.dev-name { font-size: var(--app-size-sm); font-weight: 700; color: var(--app-ink, #2d2d2d); white-space: nowrap; }
.dev-meta { font-size: var(--app-size-xs); color: var(--app-ink-muted, #999); font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.dev-tag {
  font-size: var(--app-size-xs); font-weight: 700; padding: 2px 8px; margin-left: auto; flex-shrink: 0;
  border: 1.5px solid var(--app-ink, #2d2d2d); border-radius: 3px 6px 3px 6px;
}
.dev-tag--online { background: var(--app-status-success-bg, #C8F5D0); color: var(--app-status-success-text, #2d7a2d); }

.dev-btn {
  font-size: var(--app-size-xs); font-weight: 700; padding: 4px 12px;
  border: 2px solid var(--app-ink, #2d2d2d); border-radius: 4px 8px 4px 8px;
  background: #fff; color: var(--app-ink, #2d2d2d);
  cursor: pointer; font-family: inherit; transition: all 0.12s;
  white-space: nowrap; flex-shrink: 0;
}
.dev-btn:hover { background: var(--app-highlight, #FFE066); }
.dev-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.dev-btn--primary { background: var(--app-ink, #2d2d2d); color: #fff; }
.dev-btn--primary:hover { background: var(--app-ink, #2d2d2d); opacity: 0.85; color: #fff; }
.dev-btn--danger { color: #c53030; border-color: #c53030; }
.dev-btn--danger:hover { background: var(--app-status-danger-bg, #FFE0DB); }

.opt-row { display: flex; justify-content: space-between; align-items: center; }
.opt-model { font-weight: 500; }
.opt-sub { display: flex; gap: 8px; font-size: var(--app-size-sm); color: var(--app-ink-muted, #999); margin-top: 2px; }
.opt-serial { font-family: var(--app-font-mono); font-size: var(--app-size-xs); }
</style>
