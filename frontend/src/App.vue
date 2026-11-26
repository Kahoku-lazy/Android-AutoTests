<script setup>
import { computed } from "vue"
import { useRoute } from "vue-router"
import AppSidebar from "@/shared/components/AppSidebar.vue"
import PaperDoodles from "@/shared/components/PaperDoodles.vue"

const route = useRoute()
const showSidebar = computed(() => route.path !== "/login")
</script>

<template>
  <div class="app-shell">
    <AppSidebar v-if="showSidebar" />
    <main class="main-content">
      <PaperDoodles v-if="showSidebar" />
      <div class="main-content__body">
        <router-view v-slot="{ Component }">
          <transition name="fade-slide" mode="out-in">
            <keep-alive :max="5">
              <component :is="Component" :key="route.path" />
            </keep-alive>
          </transition>
        </router-view>
      </div>
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  display: flex;

  height: 100%;
  position: relative;
  z-index: var(--z-base);
  background: var(--paper);
  overflow: hidden;
}

.main-content {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  padding: 0;
  position: relative;
  z-index: var(--z-base);
  background: transparent;
  display: flex;
  flex-direction: column;
}

.main-content__body {
  position: relative;
  z-index: var(--z-base);
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  overscroll-behavior: contain;
  display: flex;
  flex-direction: column;
}

.main-content__body :deep(.doc-page) {
  flex: 1;
  min-height: 0;
  height: auto;
  overflow: visible;
}
</style>
