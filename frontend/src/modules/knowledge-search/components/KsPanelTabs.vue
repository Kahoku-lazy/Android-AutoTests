<script setup lang="ts">
defineProps<{
  items: { key: string; label: string }[]
  modelValue: string
}>()

const emit = defineEmits<{ "update:modelValue": [key: string] }>()
</script>

<template>
  <div class="ks-tabs" role="tablist">
    <button
      v-for="item in items"
      :key="item.key"
      type="button"
      role="tab"
      class="ks-tab"
      :class="{ 'is-active': item.key === modelValue }"
      :aria-selected="item.key === modelValue"
      @click="emit('update:modelValue', item.key)"
    >
      {{ item.label }}
    </button>
  </div>
</template>

<style scoped>
.ks-tabs {
  display: inline-flex;
  gap: var(--app-space-sm);
}

.ks-tab {
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

.ks-tab:hover {
  transform: translate(-1px, -1px);
  box-shadow: 3px 3px 0 0 var(--ink);
}

.ks-tab.is-active {
  background: var(--c-case);
}

.ks-tab:focus-visible {
  outline: 2px solid var(--c-case);
  outline-offset: 2px;
}

@media (prefers-reduced-motion: reduce) {
  .ks-tab,
  .ks-tab:hover {
    transform: none;
    transition: none;
  }
}
</style>
