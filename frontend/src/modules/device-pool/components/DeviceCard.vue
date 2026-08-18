<script setup lang="ts">
/** 拍立得设备卡片 — 彩色边框 + 图钉 + 微旋转；标题=序列号，字段逐项「列名：内容」 */
import { computed } from 'vue'
import { statusTag, displayModel, deviceAddress, formatRelativeTime } from '../helpers'
import { RUNNER_OCCUPIED_PREFIXES } from '../constants'
import type { DeviceRecord } from '@/shared/types/device'

const props = defineProps<{
  device: DeviceRecord
  currentUser?: string
}>()

const emit = defineEmits<{
  lock: [device: DeviceRecord]
  release: [device: DeviceRecord]
  disconnect: [device: DeviceRecord]
  click: [device: DeviceRecord]
}>()

const status = computed(() => {
  const s = props.device.status
  if (s === 'ONLINE') return 'online'
  if (s === 'BUSY') return 'busy'
  return 'offline'
})

const statusText = computed(() => statusTag(props.device.status).text)

const isRunnerOccupied = computed(
  () =>
    !!props.device.occupied_by &&
    RUNNER_OCCUPIED_PREFIXES.some((p) => props.device.occupied_by!.startsWith(p)),
)

function go() { emit('click', props.device) }
</script>

<template>
  <div class="device-card" :class="status" role="button" tabindex="0" @click="go" @keydown.enter.prevent="go" @keydown.space.prevent="go">
    <div class="card-title" :class="status">
      <span class="card-title-text">{{ device.serial }}</span>
    </div>
    <div class="card-fields">
      <div class="card-field">
        <span class="card-field-label">设备地址</span>
        <span class="card-field-value card-field-value--mono" :title="deviceAddress(device)">{{ deviceAddress(device) }}</span>
      </div>
      <div class="card-field">
        <span class="card-field-label">型号</span>
        <span class="card-field-value">{{ displayModel(device) }}</span>
      </div>
      <div class="card-field">
        <span class="card-field-label">分辨率</span>
        <span class="card-field-value">{{ device.screen || '—' }}</span>
      </div>
      <div class="card-field">
        <span class="card-field-label">状态</span>
        <span class="card-field-value">{{ statusText }}</span>
      </div>
      <div class="card-field">
        <span class="card-field-label">最后在线</span>
        <span class="card-field-value">{{ formatRelativeTime(device.last_seen) }}</span>
      </div>
    </div>
    <div class="card-actions">
      <button
        v-if="device.connection_type === 'WIFI'"
        class="card-btn"
        @click.stop="emit('lock', device)"
      >{{ device.locked ? '已锁定' : '公开' }}</button>
      <button
        v-if="device.occupied_by && !isRunnerOccupied"
        class="card-btn unlock"
        @click.stop="emit('release', device)"
      >强制释放</button>
      <button
        v-if="device.connection_type === 'WIFI'"
        class="card-btn disconnect"
        :disabled="device.status === 'BUSY'"
        @click.stop="emit('disconnect', device)"
      >删除</button>
    </div>
  </div>
</template>

<style scoped>
/* ── 拍立得卡片 ── */
.device-card {
  background: var(--app-bg-card); border-radius: 6px 10px 6px 10px;
  padding: 8px 8px 30px 8px; cursor: pointer; position: relative;
  box-shadow: 2px 3px 0 rgba(0,0,0,0.05); transition: all 0.2s;
}
/* 边框按状态着色 */
.device-card.online { border: 3px solid var(--app-status-success); }
.device-card.busy   { border: 3px solid var(--app-status-danger); }
.device-card.offline{ border: 3px solid var(--app-offline); }

.device-card:nth-child(3n+1) { transform: rotate(-0.8deg); }
.device-card:nth-child(3n+2) { transform: rotate(0.5deg); }
.device-card:nth-child(3n+3) { transform: rotate(-0.4deg); }
.device-card:hover {
  transform: rotate(0deg) scale(1.03) !important; z-index: 5;
  box-shadow: 2px 4px 0 rgba(0,0,0,0.08);
}

/* 图钉 */
.device-card::before {
  content: ''; position: absolute; top: 4px; left: 50%; transform: translateX(-50%);
  width: 9px; height: 9px;
  background: radial-gradient(circle, var(--app-pushpin-light), var(--app-pushpin-dark));
  border-radius: 50%; box-shadow: 0 1px 1px rgba(0,0,0,0.08); z-index: 2;
}

/* 标题区（序列号） */
.card-title {
  height: 44px; border-radius: 3px 5px 3px 5px;
  display: flex; align-items: center; justify-content: center;
  padding: 0 10px; margin-bottom: 10px; border: 2px solid;
}
.card-title.online { background: var(--app-status-success-bg); border-color: var(--app-status-success); }
.card-title.busy   { background: var(--app-status-danger-bg); border-color: var(--app-status-danger); }
.card-title.offline{ background: var(--app-border-lighter); border-color: var(--app-offline); }

.card-title-text {
  font-family: var(--app-font-mono); font-size: var(--app-size-sm); font-weight: 600; color: var(--ink);
  word-break: break-all; text-align: center;
}

/* 字段列表 */
.card-fields { display: flex; flex-direction: column; gap: 4px; margin-bottom: 8px; }
.card-field { display: flex; align-items: baseline; gap: 6px; }
.card-field-label { flex-shrink: 0; font-size: var(--app-size-xs); color: var(--app-ink-muted); }
.card-field-label::after { content: '：'; }
.card-field-value {
  flex: 1; text-align: right; font-size: var(--app-size-xs); font-weight: 600; color: var(--ink);
  word-break: break-all;
}
.card-field-value--mono { font-family: var(--app-font-mono); }

/* 操作按钮 */
.card-actions { display: flex; gap: 4px; justify-content: center; flex-wrap: wrap; }
.card-btn {
  font-size: var(--app-size-xs); font-weight: 700; padding: 3px 8px;
  border-radius: 3px 6px 3px 6px; border: 1.5px solid var(--ink);
  background: var(--app-bg-card); color: var(--ink);
  cursor: pointer; font-family: inherit; transition: all 0.12s;
}
.card-btn:hover { background: var(--app-highlight); }
.card-btn.unlock:hover { background: var(--app-status-purple-bg); border-color: var(--app-status-purple-border); }
.card-btn.queue { color: var(--app-queue-text); border-color: var(--app-queue-text); }
.card-btn.queue:hover { background: var(--app-status-warning-bg); }
.card-btn.disconnect { color: var(--app-disconnect-text); border-color: var(--app-disconnect-text); }
.card-btn.disconnect:hover { background: var(--app-status-danger-bg); }
.card-btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
