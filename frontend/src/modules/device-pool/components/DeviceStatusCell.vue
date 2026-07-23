<script setup>
/** 设备状态列 — el-tag + 占用/锁定 Badge */
defineProps({
  device: { type: Object, required: true },
  statusTag: { type: Function, required: true },
})
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
        && ['runner-','ai_agent','task-','run-'].some(p => device.occupied_by.startsWith(p))"
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
  border-radius: 4px 8px 4px 8px !important; font-weight: 700 !important; font-size: 11px !important;
  border: 1.5px solid transparent !important;
}
.status-cell :deep(.el-tag--success) { background: #C8F5D0 !important; color: #2d7a2d !important; border-color: #6BCB77 !important; }
.status-cell :deep(.el-tag--warning) { background: #FFE0DB !important; color: #a03030 !important; border-color: #FFB5A7 !important; }
.status-cell :deep(.el-tag--info)    { background: #f0ede8 !important; color: #999 !important; border-color: #d4d8dc !important; }
.status-cell :deep(.el-tag--danger)  { background: #FFE0DB !important; color: #a03030 !important; border-color: #FFB5A7 !important; }
.badge {
  font-size: 10px; padding: 1px 6px; border-radius: 3px 6px 3px 6px;
  font-weight: 700; max-width: 130px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.badge-exec   { background: #FFE0DB; color: #a03030; border: 1.5px solid #FFB5A7; }
.badge-process{ background: #FFF9E0; color: #7a5a10; border: 1.5px solid #F7C948; }
.badge-locked { background: #E8DDF8; color: #5a3fa0; border: 1.5px solid #A78BFA; }
</style>
