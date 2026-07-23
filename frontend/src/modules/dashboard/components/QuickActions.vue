<script setup>
// Button → el-button (Element Plus auto-import)

defineProps({
  actions: { type: Array, default: () => [] },
})

defineEmits(['action'])
</script>

<template>
  <div class="quick-actions">
    <el-button
      v-for="(action, i) in actions"
      :key="i"
      size="default"
      class="quick-action-btn"
      :style="{ '--action-delay': (i * 70) + 'ms' }"
      @click="$emit('action', action)"
    >
      <span class="quick-action-btn__label">{{ action.label }}</span>
    </el-button>
  </div>
</template>

<style scoped>
.quick-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.quick-action-btn {
  animation: qaSlideIn 0.5s cubic-bezier(0.16,1,0.3,1) both;
  animation-delay: var(--action-delay);
}
.quick-action-btn:deep(.el-button) {
  border-radius: 4px 8px 4px 8px !important;
  border: 2px solid #2d2d2d !important;
  font-weight: 700 !important;
  transition: all 0.12s !important;
}
.quick-action-btn:deep(.el-button:hover) {
  background: #FFE066 !important;
}
.quick-action-btn__label { white-space: nowrap; }
@keyframes qaSlideIn {
  from { opacity: 0; transform: translateY(12px) scale(0.95); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}
</style>
