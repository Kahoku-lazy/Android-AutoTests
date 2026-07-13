<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { animate, stagger } from 'animejs'
import AppSidebar from '@/shared/components/AppSidebar.vue'
import { Cursor } from 'animal-island-vue'

const route = useRoute()
const transitionName = ref('fade-slide')
const showSidebar = computed(() => route.path !== '/login')

// Route transition hooks
function onBeforeEnter(el) {
  el.style.opacity = '0'
  el.style.transform = 'translateY(24px)'
}

function onAfterEnter(el) {
  animate(el, {
    opacity: [0, 1],
    translateY: [24, 0],
    duration: 420,
    ease: 'outCubic',
  })
  animate(el.querySelectorAll('.doc-section, .animal-card'), {
    opacity: [0, 1],
    translateY: [20, 0],
    delay: stagger(50),
    duration: 500,
    ease: 'outCubic',
  })
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
            @before-enter="onBeforeEnter"
            @after-enter="onAfterEnter"
          >
            <component :is="Component" />
          </transition>
        </router-view>

        <!-- 文档站底部装饰线 -->
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

/* 路由页面根节点占满主内容区，由页面内部纵向滚动 */
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
