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
  background: #fff; border-radius: 6px 10px 6px 10px;
  border: 2.5px solid var(--ink);
  box-shadow: 2px 3px 0 rgba(0,0,0,0.04);
  padding: 28px 30px; position: relative; overflow: hidden; margin-bottom: 20px;
}
.doc-hero::after { display: none; }

.doc-hero__inner {
  position: relative;
  z-index: 1;
}

.doc-hero__title {
  font-family: var(--app-font-display, Quicksand, sans-serif);
  font-size: 24px;
  font-weight: 700;
  color: var(--app-text, #4a4e69);
  margin-bottom: 6px;
  letter-spacing: -0.5px;
}

.doc-hero__desc {
  font-size: 15px;
  color: var(--app-text-secondary, #9a8c98);
  margin: 0;
  max-width: 600px;
  font-weight: 600;
}

.doc-hero__actions {
  display: flex;
  align-items: center;
  gap: 10px;
  position: relative;
  z-index: 1;
}

@media (max-width: 768px) {
  .doc-hero { padding: 24px 20px; border-radius: var(--app-radius-md, 20px); }
}
</style>
