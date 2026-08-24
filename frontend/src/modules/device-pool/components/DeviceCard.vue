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
/* ── 设备卡（轻边 + 状态色点缀） ── */
.device-card {
  background: var(--app-bg-card);
  border-radius: var(--app-radius-md);
  padding: 12px;
  cursor: pointer;
  position: relative;
  border: 1px solid var(--app-border-light);
  box-shadow: var(--app-shadow-sm);
  transition: transform var(--app-duration) var(--app-ease),
    box-shadow var(--app-duration) var(--app-ease),
    border-color var(--app-duration) var(--app-ease);
}
/* 状态色：顶部 4px 点缀条 + 标题底 */
.device-card.online::before { background: var(--app-status-success); }
.device-card.busy::before   { background: var(--app-status-danger); }
.device-card.offline::before{ background: var(--app-offline); }
.device-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  border-radius: var(--app-radius-md) var(--app-radius-md) 0 0;
}

.device-card:hover {
  transform: translate(-1px, -1px);
  box-shadow: var(--app-shadow-lg);
  border-color: var(--app-border-lighter);
}
.device-card:focus-visible {
  outline: 2px solid var(--app-status-purple);
  outline-offset: 3px;
}

/* 标题区（序列号） */
.card-title {
  height: 42px;
  border-radius: var(--app-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 10px;
  margin-bottom: 10px;
  border: 1px solid;
}
.card-title.online { background: var(--app-status-success-bg); border-color: var(--app-status-success); }
.card-title.busy   { background: var(--app-status-danger-bg); border-color: var(--app-status-danger); }
.card-title.offline{ background: var(--app-bg-subtle); border-color: var(--app-border-light); }

.card-title-text {
  font-family: var(--app-font-mono);
  font-size: var(--app-size-sm);
  font-weight: 600;
  color: var(--ink);
  word-break: break-all;
  text-align: center;
}

/* 字段列表 */
.card-fields { display: flex; flex-direction: column; gap: 5px; margin-bottom: 10px; }
.card-field { display: flex; align-items: baseline; gap: 6px; }
.card-field-label { flex-shrink: 0; font-size: var(--app-size-xs); color: var(--app-ink-muted); }
.card-field-label::after { content: '：'; }
.card-field-value {
  flex: 1;
  text-align: right;
  font-size: var(--app-size-xs);
  font-weight: 600;
  color: var(--ink);
  word-break: break-all;
}
.card-field-value--mono { font-family: var(--app-font-mono); }

/* 操作按钮 */
.card-actions { display: flex; gap: 6px; justify-content: center; flex-wrap: wrap; }
.card-btn {
  font-size: var(--app-size-xs);
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid var(--app-border-light);
  background: var(--app-bg-card);
  color: var(--ink);
  cursor: pointer;
  font-family: inherit;
  transition: all 0.12s;
}
.card-btn:hover { background: var(--app-bg-subtle); }
.card-btn.unlock:hover { background: var(--app-status-purple-bg); border-color: var(--app-status-purple-border); }
.card-btn.queue { color: var(--app-queue-text); border-color: var(--app-queue-text); }
.card-btn.queue:hover { background: var(--app-status-warning-bg); }
.card-btn.disconnect { color: var(--app-disconnect-text); border-color: var(--app-disconnect-text); }
.card-btn.disconnect:hover { background: var(--app-status-danger-bg); }
.card-btn:disabled { opacity: 0.5; cursor: not-allowed; }

@media (prefers-reduced-motion: reduce) {
  .device-card { transition: none; }
  .device-card:hover { transform: none; }
}
</style>
