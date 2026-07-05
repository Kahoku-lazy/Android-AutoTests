<script setup>
import { Title, Typewriter } from 'animal-island-vue'

defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  color: { type: String, default: 'app-yellow' },
})
</script>

<template>
  <header class="doc-hero">
    <div class="doc-hero__inner">
      <Title :color="color" size="middle" class="doc-hero__title">
        {{ title }}
      </Title>
      <Typewriter v-if="subtitle" :speed="40" trigger="mount">
        <p class="doc-hero__desc">{{ subtitle }}</p>
      </Typewriter>
    </div>
  </header>
</template>

<style scoped>
.doc-hero {
  background:
    linear-gradient(135deg, rgba(125, 195, 149, 0.95) 0%, rgba(104, 180, 150, 0.95) 100%),
    url('/animal-assets/home_bg.webp') 0 0 / 280px auto;
  padding: 24px 28px 28px;
  position: relative;
  overflow: hidden;
}

.doc-hero::after {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(45deg, rgba(255,255,255,0.08) 25%, transparent 25%),
    linear-gradient(-45deg, rgba(255,255,255,0.08) 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, rgba(255,255,255,0.08) 75%),
    linear-gradient(-45deg, transparent 75%, rgba(255,255,255,0.08) 75%);
  background-size: 20px 20px;
  background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
  opacity: 0.6;
  pointer-events: none;
}

.doc-hero__inner {
  max-width: 1600px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
}

.doc-hero__title {
  margin-bottom: 12px;
}

.doc-hero__desc {
  font-size: 15px;
  color: #fff9e6;
  margin: 0;
  max-width: 600px;
  text-shadow: 0 1px 2px rgba(0,0,0,0.15);
  opacity: 0.95;
}

@media (max-width: 768px) {
  .doc-hero { padding: 24px 20px 32px; }
}
</style>
