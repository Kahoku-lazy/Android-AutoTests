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
.status-cell { display: flex; flex-wrap: wrap; align-items: center; gap: 4px; justify-content: center; }
.status-cell :deep(.el-tag) {
  border-radius: 4px 8px 4px 8px !important; font-weight: 700 !important; font-size: var(--app-size-xs) !important;
  border: 1.5px solid transparent !important;
}
.status-cell :deep(.el-tag--success) { background: var(--app-status-success-bg) !important; color: var(--app-status-success-text) !important; border-color: var(--app-status-success) !important; }
.status-cell :deep(.el-tag--warning) { background: var(--app-status-danger-bg) !important; color: var(--app-status-danger-text) !important; border-color: var(--app-status-danger) !important; }
.status-cell :deep(.el-tag--info)    { background: var(--app-border-lighter) !important; color: var(--app-ink-muted) !important; border-color: var(--app-offline) !important; }
.status-cell :deep(.el-tag--danger)  { background: var(--app-status-danger-bg) !important; color: var(--app-status-danger-text) !important; border-color: var(--app-status-danger) !important; }
.badge {
  font-size: var(--app-size-xs); padding: 1px 6px; border-radius: 3px 6px 3px 6px;
  font-weight: 700; max-width: 130px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.badge-exec   { background: var(--app-status-danger-bg); color: var(--app-status-danger-text); border: 1.5px solid var(--app-status-danger); }
.badge-process{ background: var(--app-status-warning-bg); color: #7a5a10; border: 1.5px solid #F7C948; }
.badge-locked { background: var(--app-status-purple-bg); color: var(--app-status-purple-text); border: 1.5px solid var(--app-status-purple-border); }
</style>
