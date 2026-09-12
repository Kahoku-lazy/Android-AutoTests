<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'
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
  <div class="project-list-page">
    <WorkbenchHeader
      title="元素定位"
      subtitle="三个系统项目：Android 页面、Web 元素、API 接口"
      icon="crosshair"
      :icon-gradient="'linear-gradient(135deg,var(--c-element),#c4b5fd)'"
    />

    <div v-if="loading" class="project-list-page__body project-list-page__body--loading">
      <el-skeleton :rows="4" animated />
    </div>

    <ErrorState v-else-if="error" :message="error" @retry="loadProjects" />

    <div v-else class="project-list-page__body">
      <EmptyState
        v-if="isEmpty"
        icon="📁"
        text="暂无元素项目"
        hint="系统应预置 Android / Web / API 三个项目，请稍后重试"
      />

      <div v-else class="project-grid">
        <article
          v-for="item in projects"
          :key="item.code"
          class="project-card"
          role="button"
          tabindex="0"
          @click="enterProject(item.code)"
          @keydown.enter.prevent="enterProject(item.code)"
        >
          <div class="project-card__accent" />
          <div class="project-card__body">
            <h3 class="project-card__title">{{ item.name }}</h3>
            <p class="project-card__desc">{{ hintOf(item.code, item.description) }}</p>
            <div class="project-card__meta">
              <span>{{ item.file_count }} 个文件</span>
              <span>{{ item.updated_at?.slice(0, 10) || '—' }}</span>
            </div>
          </div>
        </article>
      </div>
    </div>
  </div>
</template>

<style scoped>
.project-list-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}
.project-list-page__body {
  flex: 1 1 0;
  min-height: 0;
  overflow-y: auto;
  padding: var(--app-space-lg);
  background-color: var(--paper);
  background-image: radial-gradient(circle, var(--dot) 0.6px, transparent 0.6px);
  background-size: 15px 15px;
}
.project-list-page__body--loading {
  max-width: 720px;
}
.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--app-space-md);
}
.project-grid > :nth-child(3n+1) { transform: rotate(-0.6deg); }
.project-grid > :nth-child(3n+2) { transform: rotate(0.4deg); }
.project-grid > :nth-child(3n+3) { transform: rotate(-0.3deg); }
.project-grid > :hover { transform: rotate(0deg) scale(1.03); z-index: 5; }
.project-card {
  position: relative;
  display: flex;
  flex-direction: column;
  border: 2px solid var(--app-border-light);
  border-radius: var(--app-radius-lg);
  background: var(--paper);
  cursor: pointer;
  transition: border-color var(--app-duration) var(--app-ease),
    box-shadow var(--app-duration) var(--app-ease);
}
.project-card:hover,
.project-card:focus-visible {
  border-color: var(--c-element);
  box-shadow: var(--app-shadow-sm);
  outline: none;
}
.project-card__accent {
  height: 4px;
  background: var(--c-element);
}
.project-card__body {
  padding: var(--app-space-md);
  flex: 1;
}
.project-card__title {
  margin: 0 0 var(--app-space-xs);
  font-size: var(--app-size-md);
  font-weight: 700;
  color: var(--ink);
}
.project-card__desc {
  margin: 0 0 var(--app-space-sm);
  font-size: var(--app-size-sm);
  color: var(--app-text-secondary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.project-card__meta {
  display: flex;
  justify-content: space-between;
  gap: var(--app-space-sm);
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
}
</style>
