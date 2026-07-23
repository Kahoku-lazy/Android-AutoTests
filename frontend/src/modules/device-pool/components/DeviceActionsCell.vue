<script setup>
/** 设备操作列 — 锁定/排队/占用/断开 */
defineProps({
  device: { type: Object, required: true },
  currentUser: { type: String, default: '' },
})
const emit = defineEmits(['lock', 'joinQueue', 'occupy', 'disconnect'])
</script>

<template>
  <div class="action-btns">
    <el-button
      size="small" type="primary"
      :class="{ 'is-locked': device.locked_by }"
      :danger="!!device.locked_by"
      :plain="!device.locked_by"
      :disabled="device.status === 'OFFLINE' || device.status === 'DISCONNECTED'
        || (!!device.locked_by && device.locked_by !== currentUser)"
      @click="emit('lock', device)"
    >{{ device.locked_by ? (device.locked_by === currentUser ? '解除锁定' : '已锁定') : '锁定' }}</el-button>
    <el-button
      v-if="device.locked_by && device.locked_by !== currentUser"
      size="small" type="warning" plain
      @click="emit('joinQueue', device)"
    >加入队列</el-button>
    <el-button
      size="small" type="primary"
      :disabled="device.status === 'OFFLINE' || device.status === 'DISCONNECTED' || !device.occupied_by"
      @click="emit('occupy', device)"
    >解除占用</el-button>
    <el-button
      v-if="device.connection_type === 'WIFI'"
      size="small" type="danger" plain
      @click="emit('disconnect', device)"
    >断开</el-button>
  </div>
</template>

<style scoped>
.action-btns { display: flex; flex-direction: column; align-items: stretch; gap: 4px; width: 100%; }
.action-btns :deep(.el-button) {
  width: 100%; margin: 0 !important; min-height: 26px; padding: 4px 10px;
  font-size: 11px; font-weight: 700; line-height: 1.2; white-space: nowrap;
  border-radius: 4px 8px 4px 8px !important; border-width: 2px !important;
}
.action-btns :deep(.el-button--primary.is-plain) {
  background: var(--app-status-purple-bg) !important; border-color: var(--app-status-purple-border) !important; color: var(--app-status-purple-text) !important;
}
.action-btns :deep(.el-button--primary.is-plain:hover) { background: #D4C8F0 !important; }
.action-btns :deep(.el-button--danger.is-plain) {
  background: var(--app-status-danger-bg) !important; border-color: var(--app-status-danger) !important; color: var(--app-status-danger-text) !important;
}
.action-btns :deep(.el-button--danger.is-plain:hover) { background: #FFD0C8 !important; }
.action-btns :deep(.el-button--warning.is-plain) {
  background: var(--app-status-warning-bg) !important; border-color: #F7C948 !important; color: #7a5a10 !important;
}
.action-btns :deep(.el-button--primary.is-disabled), .action-btns :deep(.el-button.is-disabled) {
  background: var(--app-bg-subtle) !important; border-color: var(--app-border-light) !important; color: #ccc !important;
}
</style>
