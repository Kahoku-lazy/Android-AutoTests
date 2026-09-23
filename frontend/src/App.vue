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
      <!-- 纸面涂鸦：相对主区视口固定，不随内容滚；登录页不挂 -->
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
  /* 顺 L0 的 height:100% 链（html/body/#app 都是 100%）；用 100vh 会在移动端动态工具栏下比 #app 高，触发 #app 兜底滚动 */
  height: 100%;
  position: relative;
  z-index: var(--z-base);
  background: var(--paper);
  overflow: hidden;
}

/* 主区壳：为涂鸦提供定位上下文；自身不滚，滚动下沉到 __body（策略①仍在主内容区） */
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

/* 策略① 滚动容器：内容层盖在涂鸦之上 */
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
