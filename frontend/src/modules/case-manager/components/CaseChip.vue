<script setup lang="ts">
withDefaults(
  defineProps<{
    tone: string
    text: string

    hint?: string
  }>(),
  { hint: "" },
)
</script>

<template>
  <span class="case-chip" :class="`case-chip--${tone}`" :title="hint || undefined">{{ text }}</span>
</template>

<style scoped>
.case-chip {
  display: inline-flex;
  align-items: center;
  padding: 1px var(--app-space-xs);
  border: 1.5px solid var(--ink);
  border-radius: var(--app-radius-sm);
  color: var(--ink);
  font-size: var(--app-size-sm);
  font-weight: var(--app-font-weight-bold);
  line-height: 1.4;
  white-space: nowrap;
}

.case-chip--p0 {
  background: var(--c-runner);
}

.case-chip--p1 {
  background: var(--c-dashboard);
}

.case-chip--p2 {
  background: color-mix(in srgb, var(--c-case) 32%, var(--color-white));
}

.case-chip--system {
  background: color-mix(in srgb, var(--c-workflow) 30%, var(--color-white));
}

.case-chip--business {
  background: color-mix(in srgb, var(--c-element) 24%, var(--color-white));
}

.case-chip--steps {
  background: var(--app-bg-card);
}

.case-chip--dirty {
  background: var(--c-dashboard);
}
</style>
