<script setup lang="ts">
/**
 * SerialLogTabs — 串口日志页的模块私有手稿 Tab（两枚 chip）
 *
 * 为什么不用共享 `AppTabs`：那是 Element Plus `el-tabs`，选中态是蓝色下划线，
 * 与整页手稿语言不符；共享件另有页面在用，不为本页改皮肤。
 */
defineProps<{
  items: { key: string; label: string }[]
  modelValue: string
}>()

const emit = defineEmits<{ "update:modelValue": [key: string] }>()
</script>

<template>
  <div class="sl-tabs" role="tablist">
    <button
      v-for="item in items"
      :key="item.key"
      type="button"
      role="tab"
      class="sl-tab"
      :class="{ 'is-active': item.key === modelValue }"
      :aria-selected="item.key === modelValue"
      @click="emit('update:modelValue', item.key)"
    >
      {{ item.label }}
    </button>
  </div>
</template>

<style scoped>
.sl-tabs {
  display: inline-flex;
  gap: var(--app-space-sm);
}

.sl-tab {
  border: 2px solid var(--ink);
  border-radius: 2px;
  background: var(--app-bg-card);
  color: var(--app-text-primary);
  padding: 6px var(--app-space-md);
  font-family: inherit;
  font-size: var(--app-size-sm);
  font-weight: var(--app-font-weight-heavy);
  box-shadow: 2px 2px 0 0 var(--ink);
  transition:
    transform var(--app-duration-fast) var(--app-ease),
    box-shadow var(--app-duration-fast) var(--app-ease);
}

.sl-tab:hover {
  transform: translate(-1px, -1px);
  box-shadow: 3px 3px 0 0 var(--ink);
}

.sl-tab.is-active {
  background: var(--c-dashboard);
}

.sl-tab:focus-visible {
  outline: 2px solid var(--c-dashboard);
  outline-offset: 2px;
}

@media (prefers-reduced-motion: reduce) {
  .sl-tab,
  .sl-tab:hover {
    transform: none;
    transition: none;
  }
}
</style>
