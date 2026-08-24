<script setup lang="ts">
/** KbTreeView — 知识库目录折叠树（展示 / 勾选两种模式，可自递归） */
import { ref, computed, watch } from 'vue'
import type { KbTreeNode } from '../helpers/kb-tree'

const props = defineProps<{
  nodes: KbTreeNode[]
  selectable?: boolean
  selectedKeys?: Set<string> | string[]
  showMeta?: boolean
  depth?: number
}>()

const emit = defineEmits<{
  'toggle-select': [key: string]
  'toggle-expand': [key: string]
}>()

const expanded = ref(new Set<string>())

// 顶层节点默认展开一层，便于看到目录结构
watch(
  () => props.nodes,
  (nodes) => {
    for (const n of nodes) {
      if (n.type !== 'file' && !expanded.value.has(n.key)) expanded.value.add(n.key)
    }
  },
  { immediate: true },
)

const selectedSet = computed(() => new Set<string>(props.selectedKeys || []))

function isExpanded(node: KbTreeNode) { return expanded.value.has(node.key) }
function isSelected(node: KbTreeNode) { return selectedSet.value.has(node.key) }

function onToggle(node: KbTreeNode) {
  if (node.type === 'file') return
  const key = node.key
  if (expanded.value.has(key)) expanded.value.delete(key)
  else expanded.value.add(key)
  expanded.value = new Set(expanded.value)
  emit('toggle-expand', key)
}

function formatSize(bytes?: number) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

const typeLabel = (type?: string) => {
  const map: Record<string, string> = { project_doc: '项目文档', reference: '参考', manual: '手动', generated: '自动' }
  return map[type || ''] || type || ''
}
</script>

<template>
  <div class="kb-tree-level">
    <div v-for="node in nodes" :key="node.key" class="kb-tree-node" :style="{ paddingLeft: `${(depth || 0) * 16}px` }">
      <div
        class="kb-tree-row"
        :class="{ 'has-children': node.type !== 'file', selected: selectable && isSelected(node) }"
        role="button"
        tabindex="0"
        @click="node.type === 'file' ? (selectable && emit('toggle-select', node.key)) : onToggle(node)"
        @keydown.enter.prevent="node.type === 'file' ? (selectable && emit('toggle-select', node.key)) : onToggle(node)"
        @keydown.space.prevent="node.type === 'file' ? (selectable && emit('toggle-select', node.key)) : onToggle(node)"
      >
        <span v-if="selectable" class="kb-tree-check" @click.stop>
          <el-checkbox
            :model-value="isSelected(node)"
            @change="emit('toggle-select', node.key)"
          />
        </span>
        <span class="kb-tree-arrow">{{ node.type === 'file' ? '　' : (isExpanded(node) ? '▾' : '▸') }}</span>
        <span class="kb-tree-icon">
          {{ node.type === 'dir' ? '📁' : node.type === 'group' ? '🗂️' : '📄' }}
        </span>
        <span class="kb-tree-label">{{ node.label }}</span>
        <span v-if="showMeta && node.type === 'file'" class="kb-tree-meta">
          {{ typeLabel(node.doc?.type as string) }} · {{ formatSize(node.doc?.size as number) }}
        </span>
        <span v-if="selectable && node.type === 'dir'" class="kb-tree-dir-hint">整个目录</span>
      </div>
      <KbTreeView
        v-if="node.type !== 'file' && isExpanded(node) && node.children?.length"
        :nodes="node.children"
        :selectable="selectable"
        :selected-keys="selectedKeys"
        :show-meta="showMeta"
        :depth="(depth || 0) + 1"
        @toggle-select="emit('toggle-select', $event)"
      />
    </div>
  </div>
</template>

<style scoped>
.kb-tree-level { display: flex; flex-direction: column; gap: 2px; }
.kb-tree-node { display: flex; flex-direction: column; }
.kb-tree-row {
  display: flex; align-items: center; gap: 6px; padding: 8px 10px;
  border-radius: 8px; cursor: pointer; transition: background .12s;
  border: 1.5px solid transparent;
}
.kb-tree-row:hover { background: var(--ai-teal-bg, rgba(25,200,185,.08)); }
.kb-tree-row.has-children { font-weight: 600; }
.kb-tree-row.selected { border-color: var(--ai-teal, #19c8b9); background: var(--ai-teal-bg, rgba(25,200,185,.08)); }
.kb-tree-arrow { width: 14px; font-size: var(--app-size-xs); color: var(--ai-ink-muted, #8a7b66); flex-shrink: 0; }
.kb-tree-icon { flex-shrink: 0; }
.kb-tree-label { flex: 1; min-width: 0; font-size: var(--app-size-sm); color: var(--ink, #3d3428); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.kb-tree-meta { flex-shrink: 0; font-size: var(--app-size-xs); color: var(--ai-ink-muted, #8a7b66); }
.kb-tree-dir-hint {
  flex-shrink: 0; font-size: var(--app-size-xs); font-weight: 600;
  color: var(--ai-teal, #0fa89b); background: var(--ai-teal-bg, rgba(25,200,185,.12));
  padding: 1px 8px; border-radius: 6px;
}
.kb-tree-check { display: inline-flex; flex-shrink: 0; }
</style>
