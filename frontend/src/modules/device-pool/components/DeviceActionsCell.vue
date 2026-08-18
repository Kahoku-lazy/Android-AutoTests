<script setup lang="ts">
/** 设备操作列 — 锁定/公开、强制释放、删除 */
import { computed } from 'vue'
import type { DeviceRecord } from '@/shared/types/device'
import { RUNNER_OCCUPIED_PREFIXES } from '../constants'

const props = defineProps<{
  device: DeviceRecord
  currentUser?: string
}>()
const emit = defineEmits<{
  lock: [device: DeviceRecord]
  release: [device: DeviceRecord]
  disconnect: [device: DeviceRecord]
}>()

const isRunnerOccupied = computed(() =>
  !!props.device.occupied_by &&
  RUNNER_OCCUPIED_PREFIXES.some((p) => props.device.occupied_by!.startsWith(p)),
)
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
      v-if="device.occupied_by && !isRunnerOccupied"
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
.action-bar { display: flex; flex-direction: column; align-items: stretch; gap: 4px; width: 100%; }
.action-bar :deep(.el-button) {
  width: 100%; margin: 0 !important; min-height: 26px; padding: 4px 10px;
  font-size: var(--app-size-xs); font-weight: 700; line-height: 1.2; white-space: nowrap;
  border-radius: 4px 8px 4px 8px !important; border-width: 2px !important;
}
.action-bar :deep(.el-button--primary) {
  background: var(--app-status-purple-bg) !important; border-color: var(--app-status-purple-border) !important; color: var(--app-status-purple-text) !important;
}
.action-bar :deep(.el-button--primary:hover) { background: var(--app-btn-hover-purple) !important; }
.action-bar :deep(.el-button--danger.is-plain) {
  background: var(--app-status-danger-bg) !important; border-color: var(--app-status-danger) !important; color: var(--app-status-danger-text) !important;
}
.action-bar :deep(.el-button--danger.is-plain:hover) { background: var(--app-btn-hover-danger) !important; }
.action-bar :deep(.el-button--warning.is-plain) {
  background: var(--app-status-warning-bg) !important; border-color: var(--c-dashboard) !important; color: var(--app-warning-text) !important;
}
.action-bar :deep(.el-button.is-disabled) {
  background: var(--app-bg-subtle) !important; border-color: var(--app-border-light) !important; color: var(--app-btn-disabled-color) !important;
}
</style>
