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
      <div v-if="isEmpty" style="text-align:center;color:var(--text-secondary);padding:20px 0">
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
            <AnimalButton type="primary"
              size="small"
              
              text
              @click="emit('cancel', row.serial, row.user_id)"
             danger>取消</AnimalButton>
          </template>
        </el-table-column>
      </el-table>
    </template>
  </el-popover>
</template>

<style scoped>
.queue-badge {
  background: var(--accent-pink, #f56c6c);
  color: #fff;
  padding: 4px 12px;
  border-radius: 50px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  user-select: none;
}
.queue-badge:hover {
  opacity: 0.85;
}
</style>
