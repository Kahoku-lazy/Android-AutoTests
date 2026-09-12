<script setup>
/**
 * FilterTabs — 通用筛选标签栏
 * 替代手写 filter-tab button 组，配合 useFilterTabs composable 使用。
 * tab 可选 count：展示数量角标。
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
    >
      {{ tab.label }}
      <span v-if="tab.count != null" class="filter-tab-count">{{ tab.count }}</span>
    </button>
  </div>
</template>

<style scoped>
.filter-tabs { display: flex; gap: var(--app-space-xs); flex-wrap: wrap; }
.filter-tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 14px; font-size: var(--app-size-xs); font-weight: 700;
  color: var(--app-ink-muted); background: var(--app-bg-card);
  border: 1px solid var(--app-border-light); border-radius: 999px;
  cursor: pointer; font-family: inherit; transition: all 0.15s;
}
.filter-tab:hover { color: var(--ink); border-color: var(--app-border-lighter); }
.filter-tab.active {
  color: var(--ink); background: var(--app-bg-subtle); border-color: var(--ink);
}
.filter-tab-count {
  font-family: var(--app-font-mono);
  font-size: var(--app-size-xs);
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 999px;
  background: var(--app-bg-subtle);
  border: 1px solid var(--app-border-light);
  display: inline-grid;
  place-items: center;
  color: var(--ink);
  line-height: 1;
}
.filter-tab.active .filter-tab-count {
  background: var(--app-bg-card);
  border-color: var(--ink);
}
</style>
