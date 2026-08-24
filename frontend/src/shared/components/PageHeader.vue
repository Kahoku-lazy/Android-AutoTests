<script setup>
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  color: { type: String, default: 'app-green' },
})
</script>

<template>
  <header class="doc-hero">
    <div class="doc-hero__inner">
      <h1 class="doc-hero__title">{{ title }}</h1>
      <p v-if="subtitle" class="doc-hero__desc">{{ subtitle }}</p>
    </div>
    <div v-if="$slots.actions" class="doc-hero__actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<style scoped>
.doc-hero {
  background: var(--app-bg-card); border-radius: var(--app-radius-lg);
  border: 2.5px solid var(--ink);
  box-shadow: var(--app-shadow-md);
  padding: var(--app-space-xl) 30px; position: relative; overflow: hidden; margin-bottom: var(--app-space-lg);
}
.doc-hero::after { display: none; }

.doc-hero__inner {
  position: relative;
  z-index: 1;
}

.doc-hero__title {
  font-family: var(--app-font-display);
  font-size: var(--app-size-xl);
  font-weight: 700;
  color: var(--app-text);
  margin-bottom: 6px;
  letter-spacing: -0.5px;
}

.doc-hero__desc {
  font-size: var(--app-size-md);
  color: var(--app-text-secondary);
  margin: 0;
  max-width: 600px;
  font-weight: 600;
}

.doc-hero__actions {
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
  position: relative;
  z-index: 1;
}

@media (max-width: 768px) {
  .doc-hero { padding: var(--app-space-lg) var(--app-space-lg); border-radius: var(--app-radius-md); }
}
</style>
