<script setup>
import { ref, watch } from 'vue'
import { apiGetPages } from '@/modules/element-locator/api'
import { useElementStore } from '../store'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'
import { IconLayers } from '@/shared/icons'

const store = useElementStore()
const pages = ref([])
const loading = ref(false)

/** 构建树：目录 = 可折叠标题节点（多级嵌套），页面 = 叶子 */
function buildTree(pid) {
  return pages.value
    .filter(p => (p.parent_id ?? null) === pid)
    .map(p => ({
      id: p.id,
      label: p.label || `Page #${p.id}`,
      is_folder: p.is_folder,
      package: p.package || '',
      element_count: p.element_count,
      children: p.is_folder ? buildTree(p.id) : undefined,
    }))
}

const treeData = ref([])
const expandedKeys = ref([])

watch(() => store.pickerVisible, async (v) => {
  if (!v) return
  loading.value = true
  try {
    const { data } = await apiGetPages()
    if (data.status) {
      pages.value = data.pages || []
      treeData.value = buildTree(null)
      expandedKeys.value = treeData.value.filter(n => n.is_folder).map(n => n.id)
    }
  } catch (e) { console.error(e) } finally {
    loading.value = false
  }
})

function onNodeClick(node) {
  if (!node.is_folder) {
    store.viewSavedPage(node.id)
  }
}
</script>

<template>
  <el-dialog
    v-model="store.pickerVisible"
    width="560px"
    class="saved-page-picker-dlg"
  >
    <template #header>
      <div class="picker-title">
        <span class="picker-title__text">已保存页面</span>
        <span class="picker-title__chip">只读</span>
      </div>
    </template>

    <div v-loading="loading" class="picker">
      <EmptyState
        v-if="!loading && !treeData.length"
        text="暂无已保存页面"
        hint="请先在元素定位保存页面"
      />
      <el-tree
        v-else
        :data="treeData"
        node-key="id"
        :props="{ label: 'label', children: 'children' }"
        :default-expanded-keys="expandedKeys"
        highlight-current
        :indent="22"
        @node-click="onNodeClick"
      >
        <template #default="{ data }">
          <div
            class="tree-node"
            :class="{ 'tree-node--folder': data.is_folder, 'tree-node--page': !data.is_folder }"
          >
            <div class="tree-node__row">
              <IconLayers v-if="data.is_folder" :size="13" class="tree-folder-icon" />
              <span class="tree-label">{{ data.label }}</span>
            </div>
            <span v-if="!data.is_folder" class="tree-sub">
              {{ data.package || '—' }} · 元素 {{ data.element_count }}
            </span>
          </div>
        </template>
      </el-tree>
    </div>
  </el-dialog>
</template>

<style scoped>
.picker-title {
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
  min-width: 0;
}
.picker-title__text {
  font-size: var(--app-size-lg);
  font-weight: 800;
  color: var(--ink);
  line-height: 1.3;
}
.picker-title__chip {
  flex-shrink: 0;
  font-size: var(--app-size-xs);
  font-weight: 800;
  padding: 2px 8px;
  border: 2px solid var(--ink);
  border-radius: var(--app-radius-pill);
  background: color-mix(in srgb, var(--c-element) 28%, var(--app-bg-card));
  color: var(--ink);
  line-height: 1.4;
}

.picker { min-height: 200px; max-height: 420px; overflow-y: auto; }

/* 抬高树行，两行节点不被默认一行高裁切；缩进仍由 el-tree indent 承担 */
.picker :deep(.el-tree-node__content) {
  min-height: 52px;
  height: auto;
  align-items: stretch;
  padding-top: var(--app-space-xs);
  padding-bottom: var(--app-space-xs);
}
.picker :deep(.el-tree-node__expand-icon) {
  align-self: center;
}

.tree-node {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 2px;
  min-width: 0;
  flex: 1;
  padding: var(--app-space-xs) var(--app-space-sm);
  border: 2px solid transparent;
  border-radius: var(--app-radius-sm);
  transition: background var(--app-duration-fast), border-color var(--app-duration-fast);
}
.tree-node--page {
  border-color: var(--ink);
  background: var(--app-bg-card);
  cursor: pointer;
}
.tree-node--folder {
  font-weight: 800;
  cursor: default;
}
.picker :deep(.el-tree-node__content:hover) .tree-node--page {
  background: var(--app-highlight);
}
.tree-node__row {
  display: flex;
  align-items: center;
  gap: var(--app-space-xs);
  min-width: 0;
}
.tree-folder-icon {
  color: var(--app-text-secondary);
  flex-shrink: 0;
}
.tree-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: var(--app-size-sm);
  font-weight: 700;
  color: var(--ink);
}
.tree-node--folder .tree-label { font-weight: 800; }
.tree-sub {
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
