<script setup lang="ts">
/** 设备状态列 — el-tag + 占用/锁定 Badge */
import { statusTag } from '../helpers'
import { RUNNER_OCCUPIED_PREFIXES } from '../constants'
import type { DeviceRecord } from '@/shared/types/device'

defineProps<{
  device: DeviceRecord
}>()
</script>

<template>
  <div class="status-cell">
    <el-tag
      :type="statusTag(device.status).type"
      size="small"
      effect="dark"
      round
    >{{ statusTag(device.status).text }}</el-tag>
    <el-tooltip
      v-if="device.occupied_by && device.status === 'BUSY'
        && RUNNER_OCCUPIED_PREFIXES.some(p => device.occupied_by.startsWith(p))"
      :content="device.occupied_by" placement="top"
    >
      <span class="badge badge-exec">执行中</span>
    </el-tooltip>
    <el-tooltip
      v-else-if="device.occupied_by"
      :content="device.occupied_by" placement="top"
    >
      <span class="badge badge-process">占用中: {{ device.occupied_by }}</span>
    </el-tooltip>
    <span v-else-if="device.locked_by" class="badge badge-locked">
      已绑定: {{ device.locked_by }}
    </span>
  </div>
</template>

<style scoped>
.status-cell { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; justify-content: center; }
.status-cell :deep(.el-tag) {
  border-radius: 999px !important;
  font-weight: 700 !important;
  font-size: var(--app-size-xs) !important;
  border: 1px solid transparent !important;
  padding: 0 10px !important;
}
.status-cell :deep(.el-tag--success) { background: var(--app-status-success-bg) !important; color: var(--app-status-success-text) !important; border-color: var(--app-status-success) !important; }
.status-cell :deep(.el-tag--warning) { background: var(--app-status-danger-bg) !important; color: var(--app-status-danger-text) !important; border-color: var(--app-status-danger) !important; }
.status-cell :deep(.el-tag--info)    { background: var(--app-bg-subtle) !important; color: var(--app-ink-muted) !important; border-color: var(--app-border-light) !important; }
.status-cell :deep(.el-tag--danger)  { background: var(--app-status-danger-bg) !important; color: var(--app-status-danger-text) !important; border-color: var(--app-status-danger) !important; }
.badge {
  font-size: var(--app-size-xs);
  padding: 1px 8px;
  border-radius: 999px;
  font-weight: 700;
  max-width: 130px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.badge-exec   { background: var(--app-status-danger-bg); color: var(--app-status-danger-text); border: 1px solid var(--app-status-danger); }
.badge-process{ background: var(--app-status-warning-bg); color: var(--app-warning-text); border: 1px solid var(--c-dashboard); }
.badge-locked { background: var(--app-status-purple-bg); color: var(--app-status-purple-text); border: 1px solid var(--app-status-purple-border); }
</style>
