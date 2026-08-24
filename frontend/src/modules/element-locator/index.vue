<script setup>
/** Element Locator — persistent element repository management.
 *  侧边栏「元素定位」分组下 3 个子项各对应一条路由，本容器按路由渲染对应管理器。
 */

import { computed } from 'vue'
import { useRoute } from 'vue-router'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import ElementManager from './components/ElementManager.vue'
import WebElementManager from './components/WebElementManager.vue'
import ApiEndpointManager from './components/ApiEndpointManager.vue'

const route = useRoute()

const SECTION_BY_PATH = {
  '/elements/android': 'manage',
  '/elements/web': 'web',
  '/elements/api': 'api',
}

const activeKey = computed(() => SECTION_BY_PATH[route.path] || 'manage')

const pageMeta = computed(() => {
  if (activeKey.value === 'manage') {
    return {
      title: 'Android元素管理 Android Element Manager',
      subtitle: '按页面组织元素库，维护 XPath、别名、测试点等定位信息',
    }
  }
  if (activeKey.value === 'web') {
    return {
      title: 'Web端元素管理 Web Element Manager',
      subtitle: '手动管理 Web 页面元素，支持 CSS/XPath/ID 等 12 种定位方式',
    }
  }
  if (activeKey.value === 'api') {
    return {
      title: 'API接口管理 API Endpoint Manager',
      subtitle: '管理 REST API 接口定义，配置请求体/响应体 JSON Schema',
    }
  }
  return { title: '元素定位', subtitle: '' }
})
</script>

<template>
  <div class="doc-page wb-shell">
    <WorkbenchHeader
      :title="pageMeta.title"
      :subtitle="pageMeta.subtitle"
      icon="crosshair"
      icon-gradient="linear-gradient(135deg,#C9B6F2,#a78bfa)"
    />

    <div class="locator-body">
      <ElementManager v-if="activeKey === 'manage'" />
      <WebElementManager v-else-if="activeKey === 'web'" />
      <ApiEndpointManager v-else-if="activeKey === 'api'" />
    </div>
  </div>
</template>

<style scoped>
.doc-page {
  display: flex;flex-direction: column;height: 100%;overflow: hidden;
  background: radial-gradient(circle, var(--app-paper-dot, #d4cdc0) 0.8px, transparent 0.8px);
  background-size: 14px 14px;
  background-color: var(--doodle-bg, #faf5ee);
}

.locator-body {
  flex: 1;
  min-height: 0;
  width: 100%;
  margin: 12px 0 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
</style>
