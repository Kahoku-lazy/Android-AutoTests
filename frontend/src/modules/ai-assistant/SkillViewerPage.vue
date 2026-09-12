<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import { useSkillViewer } from './composables/useSkillViewer'
import { renderSkillMarkdown } from './helpers/skill-markdown'
import type { SkillTreeNode } from './api/toolbox'

const route = useRoute()
const router = useRouter()
const skillName = computed(() => String(route.params.skillName || ''))
const {
  tree, treeLoading, treeError, selectedPath, file, fileLoading, fileError, loadTree, loadFile,
} = useSkillViewer(skillName)

const markdownHtml = computed(() => {
  if (file.value?.kind !== 'markdown' || !file.value.content) return ''
  return renderSkillMarkdown(file.value.content)
})

function onNodeClick(data: SkillTreeNode) {
  if (data.is_dir) return
  void loadFile(data.path)
}

function retryFile() {
  if (selectedPath.value) void loadFile(selectedPath.value)
}

function goBack() {
  router.push('/ai-assistant/toolbox')
}
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell ai-workbench skill-viewer-page">
    <WorkbenchHeader
      :title="skillName || 'Skill'"
      subtitle="查看 Skill 目录与文件内容"
      icon="book-open"
      icon-gradient="linear-gradient(135deg, var(--c-ai), #c084fc)"
    >
      <template #actions>
        <el-button class="wb-btn" @click="goBack">返回工具箱</el-button>
      </template>
    </WorkbenchHeader>

    <ErrorState v-if="treeError" :message="treeError" @retry="loadTree" />

    <div v-else class="doc-body sv-page">
      <aside class="sv-tree panel">
        <div class="sv-tree-label">目录</div>
        <div v-loading="treeLoading" class="sv-tree-body">
          <EmptyState v-if="!treeLoading && !tree.length" icon="📁" text="该 Skill 没有可预览文件" />
          <el-tree
            v-else
            :data="tree"
            node-key="path"
            :props="{ children: 'children', label: 'name' }"
            highlight-current
            default-expand-all
            :current-node-key="selectedPath"
            @node-click="onNodeClick"
          >
            <template #default="{ data }">
              <span class="sv-node" :class="{ active: selectedPath === data.path && !data.is_dir }">
                <span class="sv-node-icon">{{ data.is_dir ? '📁' : '📄' }}</span>
                <span class="sv-node-name">{{ data.name }}</span>
              </span>
            </template>
          </el-tree>
        </div>
      </aside>

      <section class="sv-content panel">
        <div class="sv-content-head">
          <h3 class="sv-content-title">{{ file?.name || '选择左侧文件' }}</h3>
          <p v-if="file?.path" class="sv-content-path">{{ file.path }}</p>
        </div>
        <ErrorState v-if="fileError" :message="fileError" @retry="retryFile" />
        <div v-else v-loading="fileLoading" class="sv-content-body">
          <EmptyState v-if="!file && !fileLoading" icon="📄" text="从左侧选择文件查看内容" />
          <EmptyState
            v-else-if="file?.kind === 'unsupported'"
            icon="📦"
            text="该文件类型不支持预览"
          />
          <EmptyState
            v-else-if="file?.kind === 'too_large'"
            icon="📦"
            text="文件过大，无法在页面中预览"
          />
          <article
            v-else-if="file?.kind === 'markdown'"
            class="sv-md"
            v-html="markdownHtml"
          />
          <pre v-else-if="file?.kind === 'text'" class="sv-code">{{ file.content }}</pre>
        </div>
      </section>
    </div>
  </div>
</template>

<style src="./SkillViewerPage.style.css" scoped></style>
