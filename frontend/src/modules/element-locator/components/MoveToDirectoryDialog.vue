<script setup lang="ts">
/**
 * 「移动到…」目标目录选择弹窗：只列目录（含「项目根」选项），供批量勾选后整批移动。
 */
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { LocatorTreeNode } from '../types'
import { toUiNodes, type UiTreeNode } from '../composables/useLocatorTreeMove'

interface DirOption {
  key: string
  name: string
  id: number | null
  children?: DirOption[]
}

/** 「项目根」不是目录节点，用固定 key 与 null id 表达 */
const ROOT_KEY = 'locator-root'
const ROOT_OPTION: DirOption = { key: ROOT_KEY, name: '项目根', id: null }

const props = defineProps<{
  modelValue: boolean
  treeData: LocatorTreeNode[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [directoryId: number | null]
}>()

function toDirOptions(nodes: UiTreeNode[]): DirOption[] {
  return nodes
    .filter((node) => node.type === 'directory')
    .map((node) => ({
      key: node.key,
      name: node.name,
      id: node.id,
      children: node.children?.length ? toDirOptions(node.children) : undefined,
    }))
}

const options = computed<DirOption[]>(() => [ROOT_OPTION, ...toDirOptions(toUiNodes(props.treeData))])
const selectedKey = ref(ROOT_KEY)

watch(
  () => props.modelValue,
  (opened) => {
    if (opened) selectedKey.value = ROOT_KEY
  },
)

function findOption(nodes: DirOption[], key: string): DirOption | null {
  for (const node of nodes) {
    if (node.key === key) return node
    const found = node.children ? findOption(node.children, key) : null
    if (found) return found
  }
  return null
}

function selectOption(data: DirOption) {
  selectedKey.value = data.key
}

function close() {
  emit('update:modelValue', false)
}

function confirm() {
  const target = findOption(options.value, selectedKey.value)
  if (!target) {
    ElMessage.warning('请选择目标目录')
    return
  }
  emit('confirm', target.id)
  close()
}
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    title="移动到…"
    width="420px"
    :close-on-click-modal="false"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div class="move-dialog__tree">
      <el-tree
        :data="options"
        node-key="key"
        :props="{ children: 'children', label: 'name' }"
        default-expand-all
        highlight-current
        :current-node-key="selectedKey"
        :expand-on-click-node="false"
        @node-click="selectOption"
      />
    </div>
    <template #footer>
      <el-button @click="close">取消</el-button>
      <el-button type="primary" @click="confirm">确认移动</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.move-dialog__tree {
  max-height: 320px;
  overflow-y: auto;
  border: 2px solid var(--app-border-light);
  border-radius: var(--app-radius-sm);
  padding: var(--app-space-sm);
}
</style>
