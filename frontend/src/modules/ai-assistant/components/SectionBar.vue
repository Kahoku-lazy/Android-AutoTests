<script setup lang="ts">
defineProps<{
  title: string

  count: string
}>()
</script>

<template>
  <div class="section-bar">
    <h2 class="section-bar__title">{{ title }}</h2>
    <span class="section-bar__count">{{ count }}</span>
    <span class="section-bar__spacer" />
    <slot name="action" />
  </div>
</template>

<style scoped>
.section-bar {
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
  flex-wrap: wrap;
}

.section-bar__title {
  margin: 0;
  color: var(--ink);
  font-size: var(--app-size-lg);
  font-weight: var(--app-font-weight-heavy);
}

.section-bar__count {
  color: var(--app-text-secondary);
  font-size: var(--app-size-sm);
}

.section-bar__spacer {
  flex: 1;
}
</style>
