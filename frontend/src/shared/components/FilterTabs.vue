<script setup>
/**
 * FilterTabs — 通用筛选标签栏
 * 替代手写 filter-tab button 组，配合 useFilterTabs composable 使用。
 */
defineProps({
  tabs: { type: Array, required: true },
  modelValue: { type: String, default: 'all' },
})
const emit = defineEmits(['update:modelValue'])
</script>

<template>
  <div class="filter-tabs">
    <button
      v-for="tab in tabs"
      :key="tab.key"
      type="button"
      class="filter-tab"
      :class="{ active: modelValue === tab.key }"
      @click="emit('update:modelValue', tab.key)"
    >{{ tab.label }}</button>
  </div>
</template>

<style scoped>
.filter-tabs { display: flex; gap: 4px; }
.filter-tab {
  padding: 5px 14px; font-size: var(--app-size-xs); font-weight: 700;
  color: var(--app-ink-muted); background: transparent;
  border: 2px solid transparent; border-radius: 4px 8px 4px 8px;
  cursor: pointer; font-family: inherit; transition: all 0.15s;
}
.filter-tab:hover { color: var(--ink); border-color: var(--app-border-light); }
.filter-tab.active {
  color: var(--ink); background: var(--app-highlight); border-color: var(--ink);
}
</style>
