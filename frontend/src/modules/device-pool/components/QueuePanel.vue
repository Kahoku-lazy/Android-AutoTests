<script setup>
/** QueuePanel — 排队详情 Popover 面板 per PRD §7.1 */
import { computed } from 'vue'

const props = defineProps({
  entries: { type: Array, default: () => [] },
  count: { type: Number, default: 0 },
})

const emit = defineEmits(['cancel'])

const isEmpty = computed(() => props.count === 0)

function formatTime(seconds) {
  if (!seconds || seconds < 60) return '刚刚'
  if (seconds < 3600) return `${Math.floor(seconds / 60)} 分钟`
  return `${Math.floor(seconds / 3600)} 小时`
}
</script>

<template>
  <el-popover
    trigger="click"
    placement="bottom"
    :width="420"
    :visible="undefined"
  >
    <template #reference>
      <span v-if="count" class="queue-badge">排队 {{ count }}</span>
    </template>

    <template #default>
      <div v-if="isEmpty" style="text-align:center;color:#999;padding:20px 0">
        当前无排队
      </div>
      <el-table v-else :data="entries" size="small" max-height="300">
        <el-table-column prop="user_id" label="用户" width="100" />
        <el-table-column prop="serial" label="设备" width="160" />
        <el-table-column label="等待时间" width="100">
          <template #default="{ row }">
            {{ formatTime(row.waited_seconds) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="70">
          <template #default="{ row }">
            <el-button type="danger"
              size="small"
              text
              @click="emit('cancel', row.serial, row.user_id)"
             >取消</el-button>
          </template>
        </el-table-column>
      </el-table>
    </template>
  </el-popover>
</template>

<style scoped>
.queue-badge {
  background: #FFB5A7;
  color: var(--ink);
  padding: 4px 12px;
  border-radius: 4px 8px 4px 8px;
  font-size: 11px;
  font-weight: 700;
  border: 2px solid var(--ink);
  box-shadow: 2px 2px 0 rgba(0,0,0,0.05);
  cursor: pointer;
  user-select: none;
}
.queue-badge:hover {
  opacity: 0.9;
}
</style>
