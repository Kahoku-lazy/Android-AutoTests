<script setup lang="ts">
/** 设备操作列 — 锁定/公开、强制释放、删除 */
import { computed } from 'vue'
import type { DeviceRecord } from '@/shared/types/device'
import { isRunnerOccupied } from '@/shared/helpers/deviceOccupancy'

const props = defineProps<{
  device: DeviceRecord
  currentUser?: string
}>()
const emit = defineEmits<{
  lock: [device: DeviceRecord]
  release: [device: DeviceRecord]
  disconnect: [device: DeviceRecord]
}>()

const runnerOccupied = computed(() => isRunnerOccupied(props.device.occupied_by))
</script>

<template>
  <div class="action-bar">
    <el-button
      v-if="device.connection_type === 'WIFI'"
      size="small" type="primary"
      :class="{ 'is-locked': device.locked }"
      @click="emit('lock', device)"
    >{{ device.locked ? '已锁定' : '公开' }}</el-button>
    <el-button
      v-if="device.occupied_by && !runnerOccupied"
      size="small" type="warning" plain
      @click="emit('release', device)"
    >强制释放</el-button>
    <el-button
      v-if="device.connection_type === 'WIFI'"
      size="small" type="danger" plain
      :disabled="device.status === 'BUSY'"
      @click="emit('disconnect', device)"
    >删除</el-button>
  </div>
</template>

<style scoped>
.action-bar { display: flex; flex-direction: row; align-items: center; justify-content: center; gap: 6px; width: 100%; flex-wrap: wrap; }
.action-bar :deep(.el-button) {
  margin: 0 !important;
  min-height: 26px;
  padding: var(--app-space-xs) 10px;
  font-size: var(--app-size-xs);
  line-height: 1.2;
  white-space: nowrap;
}
/* 底色保留操作语义；外形（边/圆角/阴影/文字色）由页面统一按键皮肤承担 */
.action-bar :deep(.el-button--primary) {
  background: var(--app-status-purple-bg) !important;
}
.action-bar :deep(.el-button--primary:hover) { background: var(--app-btn-hover-purple) !important; }
.action-bar :deep(.el-button--danger.is-plain) {
  background: var(--app-status-danger-bg) !important;
}
.action-bar :deep(.el-button--danger.is-plain:hover) { background: var(--app-btn-hover-danger) !important; }
.action-bar :deep(.el-button--warning.is-plain) {
  background: var(--app-status-warning-bg) !important;
}
.action-bar :deep(.el-button.is-disabled) {
  background: var(--app-bg-subtle) !important;
}
</style>
