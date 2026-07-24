<script setup>
/** 拍立得设备卡片 — 彩色边框 + 照片区 + 图钉 + 微旋转 */
import { computed } from 'vue'
import { statusTag, displayModel, connectionLabel, formatRelativeTime } from '../constants.js'

const props = defineProps({
  device: { type: Object, required: true },
  currentUser: { type: String, default: '' },
})

const emit = defineEmits(['lock', 'join-queue', 'disconnect', 'click'])

const status = computed(() => {
  const s = props.device.status
  if (s === 'ONLINE') return 'online'
  if (s === 'BUSY') return 'busy'
  return 'offline'
})

const statusText = computed(() => statusTag(props.device.status).text)

function go() { emit('click', props.device) }
</script>

<template>
  <div class="device-card" :class="status" @click="go">
    <div class="card-photo" :class="status">
      <span class="card-photo-serial">{{ device.serial }}</span>
      <span class="card-photo-badge">{{ statusText }}</span>
    </div>
    <div class="card-name">{{ displayModel(device) }}</div>
    <div class="card-info">
      {{ device.screen || '—' }} · {{ connectionLabel(device.connection_type) }} · {{ formatRelativeTime(device.last_seen) }}
    </div>
    <div class="card-actions">
      <button
        v-if="device.status !== 'OFFLINE' && device.status !== 'DISCONNECTED' && !device.locked_by"
        class="card-btn" @click.stop="emit('lock', device)">锁定</button>
      <button
        v-if="device.locked_by === currentUser"
        class="card-btn unlock" @click.stop="emit('lock', device)">解锁</button>
      <button
        v-if="device.locked_by && device.locked_by !== currentUser"
        class="card-btn queue" @click.stop="emit('join-queue', device)">排队</button>
      <button
        v-if="device.connection_type === 'WIFI'"
        class="card-btn disconnect" @click.stop="emit('disconnect', device)">断开</button>
    </div>
  </div>
</template>

<style scoped>
/* ── 拍立得卡片 ── */
.device-card {
  background: #fff; border-radius: 6px 10px 6px 10px;
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
  background: radial-gradient(circle, #e8e0d5, #a09080);
  border-radius: 50%; box-shadow: 0 1px 1px rgba(0,0,0,0.08); z-index: 2;
}

/* 照片区 */
.card-photo {
  height: 44px; border-radius: 3px 5px 3px 5px;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 10px; margin-bottom: 8px; border: 2px solid;
}
.card-photo.online { background: var(--app-status-success-bg); border-color: var(--app-status-success); }
.card-photo.busy   { background: var(--app-status-danger-bg); border-color: var(--app-status-danger); }
.card-photo.offline{ background: var(--app-border-lighter); border-color: var(--app-offline); }

.card-photo-serial {
  font-family: var(--app-font-mono); font-size: var(--app-size-xs); font-weight: 600; color: var(--ink);
}
.card-photo-badge {
  font-size: var(--app-size-xs); font-weight: 700; padding: 1px 7px;
  border-radius: 3px 6px 3px 6px; border: 1.5px solid var(--ink);
  background: rgba(255,255,255,0.7); color: var(--ink);
}

.card-name {
  font-size: var(--app-size-sm); font-weight: 700; color: var(--ink); text-align: center; margin-bottom: 2px;
}
.card-info {
  font-size: var(--app-size-xs); color: var(--app-ink-muted); text-align: center; margin-bottom: 6px;
}

/* 操作按钮 */
.card-actions { display: flex; gap: 4px; justify-content: center; flex-wrap: wrap; }
.card-btn {
  font-size: var(--app-size-xs); font-weight: 700; padding: 3px 8px;
  border-radius: 3px 6px 3px 6px; border: 1.5px solid var(--ink);
  background: #fff; color: var(--ink);
  cursor: pointer; font-family: inherit; transition: all 0.12s;
}
.card-btn:hover { background: var(--app-highlight); }
.card-btn.unlock:hover { background: var(--app-status-purple-bg); border-color: var(--app-status-purple-border); }
.card-btn.queue { color: #b08800; border-color: #b08800; }
.card-btn.queue:hover { background: var(--app-status-warning-bg); }
.card-btn.disconnect { color: #c53030; border-color: #c53030; }
.card-btn.disconnect:hover { background: var(--app-status-danger-bg); }
</style>
