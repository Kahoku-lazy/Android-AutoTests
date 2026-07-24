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
  background: var(--doodle-bg, #faf5ee);
  overflow: hidden;
}

.main-content {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  padding: 0;
  position: relative;
  z-index: 1;
  background: transparent;
  display: flex;
  flex-direction: column;
}

.main-content :deep(.doc-page) {
  flex: 1;
  min-height: 0;
  height: 100%;
}

</style>
