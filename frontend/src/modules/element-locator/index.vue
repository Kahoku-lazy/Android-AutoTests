<script setup>
/** Element Locator — persistent element repository management. */

import { ref, computed } from 'vue'
import AppTabs from "@/shared/components/AppTabs.vue";
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import ElementManager from './components/ElementManager.vue'
import WebElementManager from './components/WebElementManager.vue'
import ApiEndpointManager from './components/ApiEndpointManager.vue'

const activeTab = ref('manage')
const tabs = [
  { key: 'manage', label: '📋 Android元素管理' },
  { key: 'web', label: '🌐 Web端元素' },
  { key: 'api', label: '📡 API接口' },
]

const pageMeta = computed(() => {
  if (activeTab.value === 'manage') {
    return {
      title: 'Android元素管理 Android Element Manager',
      subtitle: '按页面组织元素库，维护 XPath、别名、测试点等定位信息',
    }
  }
  if (activeTab.value === 'web') {
    return {
      title: 'Web端元素管理 Web Element Manager',
      subtitle: '手动管理 Web 页面元素，支持 CSS/XPath/ID 等 12 种定位方式',
    }
  }
  if (activeTab.value === 'api') {
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

    <AppTabs :items="tabs" v-model="activeTab" :leaf-animation="true" :shadow="true" class="locator-tabs">
      <template #manage>
        <div v-show="activeTab === 'manage'" class="doc-body">
          <ElementManager />
        </div>
      </template>

      <template #web>
        <div v-show="activeTab === 'web'" class="doc-body">
          <WebElementManager />
        </div>
      </template>

      <template #api>
        <div v-show="activeTab === 'api'" class="doc-body">
          <ApiEndpointManager />
        </div>
      </template>
    </AppTabs>
  </div>
</template>

<style scoped>
.doc-page {
  display: flex;flex-direction: column;height: 100%;overflow: hidden;
  background: radial-gradient(circle, var(--app-paper-dot, #d4cdc0) 0.8px, transparent 0.8px);
  background-size: 14px 14px;
  background-color: var(--doodle-bg, #faf5ee);
}

.locator-tabs {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin-top: 12px;
}

.doc-page :deep(.locator-tabs.el-tabs) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.doc-page :deep(.locator-tabs.el-tabs > .el-tabs__content) {
  flex: 1;
  min-height: 0;
  width: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding-top: 8px;
}
.doc-page :deep(.locator-tabs.el-tabs > .el-tabs__content > .el-tab-pane) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.doc-page :deep(.locator-tabs.el-tabs > .el-tabs__header) {
  margin: 0 0 8px;
  width: 100%;
}
.doc-page :deep(.locator-tabs .el-tabs__nav-wrap),
.doc-page :deep(.locator-tabs .el-tabs__nav-scroll) {
  width: 100%;
}
.doc-page :deep(.locator-tabs .el-tabs__nav) {
  display: flex;
  width: 100%;
  box-sizing: border-box;
  border-radius: var(--app-radius-md);
}
.doc-page :deep(.locator-tabs .el-tabs__item) {
  flex: 1;
  width: auto;
  max-width: none;
  justify-content: center;
  text-align: center;
  height: 40px;
  padding: 0 12px;
  border-radius: var(--app-radius-sm);
}

.doc-page :deep(.locator-tabs.el-tabs > .el-tabs__content > .el-tab-pane) {
  flex: 1;
  min-height: 0;
  width: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.doc-page :deep(.locator-tabs.el-tabs > .el-tabs__content > .el-tab-pane > .doc-body) {
  flex: 1;
  min-height: 0;
  width: 100%;
  max-width: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Doodle Craft — override AppTabs defaults */
.locator-tabs :deep(.el-tabs__nav) {
  gap: 0 !important; padding: 0 !important;
  border-radius: 0 !important;
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}
.locator-tabs :deep(.el-tabs__item) {
  height: 36px !important; padding: 0 20px !important;
  border-radius: 4px 8px 0 0 !important;
  color: var(--app-ink-muted, #999) !important;
  font-weight: 700 !important; font-size: var(--app-size-sm) !important;
  border: 2px solid transparent !important;
  background: transparent !important;
}
.locator-tabs :deep(.el-tabs__item:hover) {
  color: var(--app-ink, #2d2d2d) !important;
  background: rgba(0,0,0,0.03) !important;
}
.locator-tabs :deep(.el-tabs__item.is-active) {
  color: var(--app-ink, #2d2d2d) !important;
  background: var(--app-bg-card) !important;
  border-color: var(--app-ink, #2d2d2d) !important;
  border-bottom-color: var(--app-bg-card) !important;
}
.locator-tabs :deep(.el-tabs__active-bar) {
  display: none !important;
}
.locator-tabs :deep(.el-tabs__header) {
  border-bottom: 2px solid var(--app-ink, #2d2d2d) !important;
  margin-bottom: 0 !important;
}
</style>
