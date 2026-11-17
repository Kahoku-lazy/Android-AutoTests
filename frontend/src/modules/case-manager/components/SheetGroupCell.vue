<script setup lang="ts">
/**
 * 组头条单元：分组视图里合并行的内容。
 *
 * 只在「第一个可见列」的插槽里真正渲染——其余列被 span-method 合并掉。
 */
defineProps<{
  name: string
  count: number
}>()
</script>

<template>
  <span class="case-group">
    {{ name }}
    <em class="case-group__count">{{ count }} 条</em>
  </span>
</template>

<style scoped>
.case-group {
  display: inline-flex;
  align-items: baseline;
  gap: var(--app-space-sm);
  font-size: var(--app-size-sm);
  font-weight: var(--app-font-weight-heavy);
  color: var(--app-text-primary);
}

.case-group__count {
  font-family: var(--app-font-mono);
  font-size: var(--app-size-xs);
  font-style: normal;
  font-weight: var(--app-font-weight-bold);
  color: var(--app-text-secondary);
}
</style>
