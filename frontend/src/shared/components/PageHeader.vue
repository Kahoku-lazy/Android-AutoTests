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
  </header>
</template>

<style scoped>
.doc-hero {
  background: var(--app-glass-heavy, rgba(255,255,255,0.65));
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border-radius: var(--app-radius-lg, 28px);
  border: 1px solid var(--app-glass-border, rgba(255,255,255,0.55));
  box-shadow: var(--app-shadow-sm, 0 4px 15px rgba(31,38,135,0.04));
  padding: 28px 30px;
  position: relative;
  overflow: hidden;
  margin-bottom: 20px;
}

.doc-hero::after {
  content: '';
  position: absolute;
  top: -30px; right: -30px;
  width: 140px; height: 140px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(142,200,160,0.3), transparent);
  pointer-events: none;
}

.doc-hero__inner {
  position: relative;
  z-index: 1;
}

.doc-hero__title {
  font-family: var(--app-font-display, Quicksand, sans-serif);
  font-size: 22px;
  font-weight: 700;
  color: var(--app-text, #3D4A3B);
  margin-bottom: 6px;
  letter-spacing: -0.5px;
}

.doc-hero__desc {
  font-size: 14px;
  color: var(--app-text-secondary, #7A8B73);
  margin: 0;
  max-width: 600px;
  font-weight: 600;
}

@media (max-width: 768px) {
  .doc-hero { padding: 24px 20px; border-radius: var(--app-radius-md, 20px); }
}
</style>
