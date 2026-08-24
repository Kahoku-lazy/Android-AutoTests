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
    :model-value="store.pickerVisible"
    title="打开元素定位已保存页面（只读）"
    width="560px"
    @update:model-value="(v) => (store.pickerVisible = v)"
  >
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
        @node-click="onNodeClick"
      >
        <template #default="{ data }">
          <span class="tree-node" :class="{ 'tree-node--folder': data.is_folder }">
            <IconLayers v-if="data.is_folder" :size="13" class="tree-folder-icon" />
            <span class="tree-label">{{ data.label }}</span>
            <span v-if="!data.is_folder" class="tree-sub">{{ data.package || '—' }} · 元素 {{ data.element_count }}</span>
          </span>
        </template>
      </el-tree>
    </div>
  </el-dialog>
</template>

<style scoped>
.picker { min-height: 200px; max-height: 420px; overflow-y: auto; }
.tree-node { display: flex; align-items: center; gap: 6px; }
.tree-node--folder { font-weight: 700; }
.tree-folder-icon { color: var(--app-text-secondary); flex-shrink: 0; }
.tree-label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tree-sub { font-size: var(--app-size-xs); color: var(--app-text-secondary); white-space: nowrap; }
</style>
