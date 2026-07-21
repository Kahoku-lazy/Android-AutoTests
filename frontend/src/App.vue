<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppSidebar from '@/shared/components/AppSidebar.vue'

const route = useRoute()
const showSidebar = computed(() => route.path !== '/login')
</script>

<template>
  <div class="app-shell">
    <AppSidebar v-if="showSidebar" />
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <keep-alive :max="5">
          <component :is="Component" :key="route.path" />
        </keep-alive>
      </router-view>
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  display: flex;
  height: 100vh;
  position: relative;
  z-index: 1;
  background:
    radial-gradient(circle at 16% 10%, var(--app-sky-cloud, rgba(255,255,255,0.82)), transparent 28%),
    radial-gradient(circle at 84% 18%, rgba(162,210,255,0.5), transparent 32%),
    radial-gradient(circle at 78% 90%, rgba(63,158,216,0.42), transparent 36%),
    radial-gradient(circle at 14% 88%, rgba(111,185,141,0.42), transparent 34%),
    linear-gradient(135deg, var(--app-sky, #dff5ff) 0%, var(--app-blue-light, #bde0fe) 38%, var(--app-ocean-soft, #a7d8ee) 68%, var(--app-forest-soft, #d6f2da) 100%);
  background-size: 180% 180%;
  animation: appShellGradient 15s ease infinite;
  overflow: hidden;
}

.app-shell::before,
.app-shell::after {
  content: '';
  position: absolute;
  border-radius: 50%;
  filter: blur(64px);
  opacity: 0.72;
  pointer-events: none;
  z-index: 0;
}

.app-shell::before {
  top: -120px;
  left: -80px;
  width: 400px;
  height: 400px;
  background: var(--app-sky-cloud, rgba(255,255,255,0.82));
}

.app-shell::after {
  right: -90px;
  bottom: -120px;
  width: 340px;
  height: 340px;
  background: var(--app-ocean, #3f9ed8);
}

@keyframes appShellGradient {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.main-content {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  padding: 0;
  position: relative;
  z-index: 1;
  background: rgba(255,255,255,0.12);
  display: flex;
  flex-direction: column;
}

.main-content::before {
  content: '';
  position: absolute;
  left: 14%;
  bottom: -120px;
  width: 360px;
  height: 300px;
  border-radius: 50%;
  background: var(--app-forest, #6fb98d);
  filter: blur(80px);
  opacity: 0.48;
  pointer-events: none;
  z-index: -1;
}

.main-content :deep(.doc-page) {
  flex: 1;
  min-height: 0;
  height: 100%;
}

</style>
