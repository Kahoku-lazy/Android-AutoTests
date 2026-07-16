<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { pageEnter, pageLeave, staggerIn, iconBounce } from '@/shared/animations.js'
import AppSidebar from '@/shared/components/AppSidebar.vue'
import { Cursor } from 'animal-island-vue'

const route = useRoute()
const transitionName = ref('fade-slide')
const showSidebar = computed(() => route.path !== '/login')

function onBeforeEnter(el) {
  el.style.opacity = '0'
  el.style.transform = 'translateY(20px)'
}

function onEnter(el, done) {
  pageEnter(el, () => {
    const sections = el.querySelectorAll(
      '.doc-section, .animal-card, .agent-card, .kpi-card, .task-card, .wb-header'
    )
    if (sections.length) staggerIn(sections, 45)
    const mark = el.querySelector('.brand-mark')
    if (mark) iconBounce(mark)
    done()
  })
}

function onLeave(el, done) {
  pageLeave(el, done)
}
</script>

<template>
  <Cursor :force-all="false">
    <div class="app-shell">
      <AppSidebar v-if="showSidebar" />
      <main class="main-content">
        <router-view v-slot="{ Component }">
          <transition
            :name="transitionName"
            mode="out-in"
            @before-enter="onBeforeEnter"
            @enter="onEnter"
            @leave="onLeave"
          >
            <component :is="Component" :key="route.path" />
          </transition>
        </router-view>

        <img
          v-if="showSidebar"
          src="/animal-assets/guide-bg-line.webp"
          alt=""
          class="guide-line"
          loading="lazy"
          decoding="async"
        />
      </main>
    </div>
  </Cursor>
</template>

<style scoped>
.app-shell {
  display: flex;
  height: 100vh;
  position: relative;
  z-index: 1;
  background: var(--animal-bg-color, #f8f8f0);
}

.main-content {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  padding: 0;
  position: relative;
  z-index: 1;
  background: url('/animal-assets/content_bg_pc.jpg') center / auto repeat;
  display: flex;
  flex-direction: column;
}

.main-content :deep(.doc-page) {
  flex: 1;
  min-height: 0;
  height: 100%;
}

.guide-line {
  position: fixed;
  left: var(--side-w, 220px);
  right: 0;
  bottom: 0;
  width: auto;
  pointer-events: none;
  z-index: -1;
  opacity: 0.55;
}
</style>
