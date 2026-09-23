<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import SketchCard from '@/shared/components/SketchCard.vue'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'
import SkeletonCard from '@/shared/components/patterns/SkeletonCard.vue'
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
  <div class="doc-page doc-page--fixed wb-shell locator-workbench locator-project-list">
    <WorkbenchHeader
      title="元素定位"
      subtitle="系统内置的 Android 页面与控件定位库"
      icon="crosshair"
      :icon-gradient="'linear-gradient(135deg,var(--c-element),var(--locator-header-icon-end))'"
    />

    <div v-if="loading" class="doc-body">
      <SkeletonCard variant="list" :lines="4" />
    </div>

    <ErrorState v-else-if="error" :message="error" @retry="loadProjects" />

    <div v-else class="doc-body">
      <EmptyState
        v-if="isEmpty"
        icon="📁"
        text="暂无元素项目"
        hint="系统应预置 Android 项目，请稍后重试"
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
.locator-project-list .doc-body {
  overflow-y: auto;
  padding: var(--app-space-lg);
}
.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--app-space-md);
}
</style>
