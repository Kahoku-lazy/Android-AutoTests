<script setup>
/** 拍立得设备卡片 — 彩色边框 + 照片区 + 图钉 + 微旋转 */
import { computed } from 'vue'

const props = defineProps({
  device: { type: Object, required: true },
  statusTag: { type: Function, required: true },
  displayModel: { type: Function, required: true },
  connectionLabel: { type: Function, required: true },
  formatRelativeTime: { type: Function, required: true },
  currentUser: { type: String, default: '' },
})

const emit = defineEmits(['lock', 'join-queue', 'disconnect', 'click'])

const status = computed(() => {
  const s = props.device.status
  if (s === 'ONLINE') return 'online'
  if (s === 'BUSY') return 'busy'
  return 'offline'
})

const statusText = computed(() => props.statusTag(props.device.status).text)

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
.device-card.online { border: 2.5px solid #6BCB77; }
.device-card.busy   { border: 2.5px solid #FFB5A7; }
.device-card.offline{ border: 2.5px solid #d4d8dc; }

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
.card-photo.online { background: #C8F5D0; border-color: #6BCB77; }
.card-photo.busy   { background: #FFE0DB; border-color: #FFB5A7; }
.card-photo.offline{ background: #f0ede8; border-color: #d4d8dc; }

.card-photo-serial {
  font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 600; color: #2d2d2d;
}
.card-photo-badge {
  font-size: 9px; font-weight: 700; padding: 1px 7px;
  border-radius: 3px 6px 3px 6px; border: 1.5px solid #2d2d2d;
  background: rgba(255,255,255,0.7); color: #2d2d2d;
}

.card-name {
  font-size: 12px; font-weight: 700; color: #2d2d2d; text-align: center; margin-bottom: 2px;
}
.card-info {
  font-size: 9px; color: #999; text-align: center; margin-bottom: 6px;
}

/* 操作按钮 */
.card-actions { display: flex; gap: 4px; justify-content: center; flex-wrap: wrap; }
.card-btn {
  font-size: 9px; font-weight: 700; padding: 3px 8px;
  border-radius: 3px 6px 3px 6px; border: 1.5px solid #2d2d2d;
  background: #fff; color: #2d2d2d;
  cursor: pointer; font-family: inherit; transition: all 0.12s;
}
.card-btn:hover { background: #FFE066; }
.card-btn.unlock:hover { background: #E8DDF8; border-color: #A78BFA; }
.card-btn.queue { color: #b08800; border-color: #b08800; }
.card-btn.queue:hover { background: #FFF9E0; }
.card-btn.disconnect { color: #c53030; border-color: #c53030; }
.card-btn.disconnect:hover { background: #FFE0DB; }
</style>
