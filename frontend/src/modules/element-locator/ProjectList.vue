<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import SketchCard from '@/shared/components/SketchCard.vue'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'
import { sketchTiltAt, sketchToneAt } from '@/shared/helpers/sketchCard'
import { useLocatorProjects } from './composables/useLocatorProjects'
import { PROJECT_HINTS, isLocatorProjectCode } from './types'

const router = useRouter()
const { projects, loading, error, isEmpty, loadProjects } = useLocatorProjects()

onMounted(() => {
  loadProjects()
})

function hintOf(code: string, description: string) {
  if (description) return description
  return isLocatorProjectCode(code) ? PROJECT_HINTS[code] : '暂无描述'
}

function enterProject(code: string) {
  router.push(`/elements/projects/${code}`)
}
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell project-list-page">
    <WorkbenchHeader
      title="元素定位"
      subtitle="三个系统项目：Android 页面、Web 元素、API 接口"
      icon="crosshair"
      :icon-gradient="'linear-gradient(135deg,var(--c-element),var(--locator-header-icon-end))'"
    />

    <div v-if="loading" class="doc-body project-list-page__loading">
      <el-skeleton :rows="4" animated />
    </div>

    <ErrorState v-else-if="error" :message="error" @retry="loadProjects" />

    <div v-else class="doc-body">
      <EmptyState
        v-if="isEmpty"
        icon="📁"
        text="暂无元素项目"
        hint="系统应预置 Android / Web / API 三个项目，请稍后重试"
      />

      <div v-else class="project-grid">
        <SketchCard
          v-for="(item, index) in projects"
          :key="item.code"
          :title="item.name"
          :description="hintOf(item.code, item.description)"
          :meta="`${item.file_count} 个文件 · ${item.updated_at?.slice(0, 10) || '—'}`"
          icon="crosshair"
          :tone="sketchToneAt(index)"
          :tilt="sketchTiltAt(index)"
          @activate="enterProject(item.code)"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 页面根/主体骨架由 .doc-page / .doc-body 提供，这里只留本页增量 */
/* 页头图标渐变末端色：tokens.css 未登记 #c4b5fd，登记在本页根作用域，随根元素继承给页头图标块 */
.project-list-page {
  --locator-header-icon-end: var(--color-indigo-84) /* -> --color-indigo-84 */;
}
.project-list-page .doc-body {
  overflow-y: auto;
  padding: var(--app-space-lg);
  background-color: var(--paper);
}
.project-list-page__loading {
  max-width: 720px;
}
.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--app-space-md);
}
</style>
