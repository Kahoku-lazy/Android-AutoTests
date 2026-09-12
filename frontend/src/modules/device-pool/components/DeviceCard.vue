<script setup lang="ts">
/** 设备卡片 — 横向长方形极简几何 */
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

const isWifi = computed(() => props.device.connection_type === 'WIFI')

const isRunnerOccupied = computed(
  () =>
    !!props.device.occupied_by &&
    RUNNER_OCCUPIED_PREFIXES.some((p) => props.device.occupied_by!.startsWith(p)),
)

function go() {
  emit('click', props.device)
}
</script>

<template>
  <div
    class="device-card"
    :class="status"
    role="button"
    tabindex="0"
    @click="go"
    @keydown.enter.prevent="go"
    @keydown.space.prevent="go"
  >
    <div class="card-main">
      <div class="card-identity">
        <div class="card-title-row">
          <p class="card-model">{{ displayModel(device) }}</p>
          <span class="status-chip" :class="status">
            <span class="geo" :class="status === 'busy' ? 'geo--triangle' : 'geo--diamond'" aria-hidden="true" />
            {{ statusText }}
          </span>
        </div>
        <code class="card-serial" :title="device.serial">{{ device.serial }}</code>
      </div>

      <div class="card-meta">
        <div class="meta-cell">
          <span class="meta-k">地址</span>
          <span class="meta-v meta-v--mono" :title="deviceAddress(device)">{{ deviceAddress(device) }}</span>
        </div>
        <div class="meta-cell">
          <span class="meta-k">分辨率</span>
          <span class="meta-v meta-v--mono">{{ device.screen || '—' }}</span>
        </div>
        <div class="meta-cell">
          <span class="meta-k">连接</span>
          <span class="meta-v">{{ isWifi ? 'Wi‑Fi' : 'USB' }}</span>
        </div>
        <div class="meta-cell">
          <span class="meta-k">活跃</span>
          <span class="meta-v">{{ formatRelativeTime(device.last_seen) }}</span>
        </div>
      </div>
    </div>

    <div class="card-foot">
      <span class="tag" :class="isWifi ? 'tag--wifi' : 'tag--usb'">{{ isWifi ? 'Wi‑Fi' : 'USB' }}</span>
      <span
        v-if="device.locked_by"
        class="tag tag--lock"
        :title="`锁定者: ${device.locked_by}`"
      >锁定 · {{ device.locked_by }}</span>
      <span v-else class="tag tag--open">公开</span>

      <div class="card-actions">
        <button
          v-if="isWifi"
          type="button"
          class="card-btn"
          @click.stop="emit('lock', device)"
        >{{ device.locked ? '解锁' : '锁定' }}</button>
        <button
          v-if="device.occupied_by && !isRunnerOccupied"
          type="button"
          class="card-btn card-btn--warn"
          @click.stop="emit('release', device)"
        >释放</button>
        <button
          v-if="isWifi"
          type="button"
          class="card-btn card-btn--ghost"
          :disabled="device.status === 'BUSY'"
          @click.stop="emit('disconnect', device)"
        >删除</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.device-card {
  --card-accent: var(--c-device);
  background: var(--app-bg-card);
  border: 2px solid var(--ink);
  border-radius: var(--app-radius-md);
  box-shadow: var(--app-shadow-sm);
  padding: 0;
  overflow: hidden;
  cursor: pointer;
  position: relative;
  display: flex;
  flex-direction: column;
  width: 100%;
  /* 横向长方形：宽 > 高 */
  aspect-ratio: 2.2 / 1;
  min-height: 132px;
  max-height: 168px;
  transition: transform var(--app-duration) var(--app-ease);
}
.device-card.busy { --card-accent: var(--c-dashboard); }
.device-card.offline { --card-accent: var(--app-border-light); }

.device-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: var(--card-accent);
}

.device-card:hover { z-index: 2; }
.device-card:focus-visible {
  outline: 2px solid var(--app-status-purple);
  outline-offset: 3px;
}

.card-main {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: var(--app-space-sm);
  padding: 10px 12px 6px 14px;
}

.card-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--app-space-sm);
  min-width: 0;
}
.card-model {
  margin: 0;
  font-size: var(--app-size-sm);
  font-weight: 800;
  line-height: 1.2;
  color: var(--ink);
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.card-serial {
  margin: var(--app-space-xs) 0 0;
  font-family: var(--app-font-mono);
  font-size: var(--app-size-xs);
  font-weight: 700;
  color: var(--app-nav-text);
  background: var(--app-bg-subtle);
  border: 1px solid var(--ink);
  border-radius: var(--app-radius-sm);
  padding: 1px 5px;
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-chip {
  display: inline-flex;
  align-items: center;
  gap: var(--app-space-xs);
  padding: 2px 6px;
  border: 1px solid var(--ink);
  border-radius: var(--app-radius-sm);
  font-size: var(--app-size-xs);
  font-weight: 800;
  white-space: nowrap;
  flex-shrink: 0;
}
.status-chip.online {
  background: var(--app-status-success-bg);
  color: var(--app-status-success-text);
}
.status-chip.busy {
  background: var(--app-status-warning-bg);
  color: var(--app-warning-text);
}
.status-chip.offline {
  background: var(--app-bg-subtle);
  color: var(--app-ink-muted);
}

.geo { flex-shrink: 0; display: inline-block; }
.geo--diamond {
  width: 8px;
  height: 8px;
  border: 1px solid var(--ink);
  background: var(--c-device);
  transform: rotate(45deg);
  border-radius: 1px;
}
.geo--triangle {
  width: 0;
  height: 0;
  border-left: 5px solid transparent;
  border-right: 5px solid transparent;
  border-bottom: 9px solid var(--c-dashboard);
}

/* 四字段横排，压低纵向高度 */
.card-meta {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--app-space-sm);
  padding-top: 6px;
  border-top: 1px solid var(--app-border-light);
  background: transparent;
}
.meta-k {
  display: block;
  font-size: var(--app-size-xs);
  font-weight: 500;
  color: var(--app-ink-muted);
  margin-bottom: 1px;
}
.meta-v {
  font-size: var(--app-size-xs);
  font-weight: 500;
  color: var(--ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.3;
}
.meta-v--mono { font-family: var(--app-font-mono); }

.card-foot {
  flex-shrink: 0;
  padding: 6px 12px var(--app-space-sm) 14px;
  display: flex;
  flex-wrap: nowrap;
  gap: var(--app-space-xs);
  align-items: center;
  border-top: 1px solid var(--app-border-light);
  min-height: 0;
}
.tag {
  font-size: var(--app-size-xs);
  font-weight: 800;
  padding: 1px 5px;
  border: 1px solid var(--ink);
  border-radius: var(--app-radius-sm);
  white-space: nowrap;
}
.tag--wifi {
  background: color-mix(in srgb, var(--c-workflow) 40%, white);
  color: var(--ink);
}
.tag--usb {
  background: color-mix(in srgb, var(--c-device) 35%, white);
  color: var(--ink);
}
.tag--lock {
  background: var(--app-status-purple-bg);
  color: var(--app-status-purple-text);
  border-color: var(--app-status-purple-border);
  max-width: 96px;
  overflow: hidden;
  text-overflow: ellipsis;
}
.tag--open {
  background: var(--app-bg-subtle);
  color: var(--app-ink-muted);
  border-color: var(--app-border-light);
}

.card-actions {
  margin-left: auto;
  display: flex;
  gap: var(--app-space-xs);
  flex-shrink: 0;
}
.card-btn {
  border: 1.5px solid var(--ink);
  background: var(--app-bg-card);
  border-radius: var(--app-radius-sm);
  padding: 2px var(--app-space-sm);
  font: inherit;
  font-size: var(--app-size-xs);
  font-weight: 800;
  color: var(--ink);
  cursor: pointer;
  transition: background 0.12s, transform 0.12s;
}
.card-btn:hover {
  background: var(--app-highlight);
  transform: translate(1px, 1px);
}
.card-btn--ghost { border-style: dashed; }
.card-btn--warn { background: var(--app-status-warning-bg); }
.card-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

@media (max-width: 720px) {
  .device-card {
    aspect-ratio: 1.6 / 1;
    max-height: none;
  }
  .card-meta {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    row-gap: var(--app-space-xs);
  }
}

@media (prefers-reduced-motion: reduce) {
  .device-card { transition: none; }
}
</style>
