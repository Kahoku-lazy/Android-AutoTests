<script setup lang="ts">
/**
 * 可编辑单元格：默认只渲染纯文本，双击才进入编辑态（挂载 el-input 并自动聚焦）。
 * Enter 提交、Esc 取消、失焦提交；校验不通过时就地提示并恢复原值。
 */
import { nextTick, ref } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps<{
  value: string
  placeholder?: string
  /** 返回中文原因表示非法；null 表示通过 */
  validate?: (value: string) => string | null
}>()

const emit = defineEmits<{ commit: [value: string] }>()

const editing = ref(false)
const draft = ref(props.value)
const inputRef = ref<{ focus: () => void } | null>(null)

function startEdit() {
  draft.value = props.value
  editing.value = true
  void nextTick(() => inputRef.value?.focus())
}

function cancel() {
  editing.value = false
  draft.value = props.value
}

function commit() {
  if (!editing.value) return
  if (draft.value === props.value) {
    editing.value = false
    return
  }
  const reason = props.validate?.(draft.value) ?? null
  if (reason) {
    ElMessage.error(reason)
    cancel()
    return
  }
  editing.value = false
  emit('commit', draft.value)
}
</script>

<template>
  <el-input
    v-if="editing"
    ref="inputRef"
    v-model="draft"
    size="small"
    @click.stop
    @blur="commit"
    @keyup.enter="commit"
    @keyup.esc="cancel"
  />
  <span
    v-else
    class="editable-cell"
    :title="value || placeholder"
    @dblclick.stop="startEdit"
  >
    {{ value || '—' }}
  </span>
</template>

<style scoped>
.editable-cell {
  display: block;
  min-height: 20px;
  cursor: text;
  color: var(--ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
