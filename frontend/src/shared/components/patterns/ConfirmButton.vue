<template>
  <el-button v-bind="$attrs" @click.stop="handleClick">
    <slot />
  </el-button>
</template>

<script setup>
import { ElMessageBox } from 'element-plus'

const props = defineProps({
  /** Confirmation message shown in the dialog */
  message: { type: String, required: true },
  /** Dialog title */
  title: { type: String, default: '确认操作' },
  /** Text for the confirm button */
  confirmText: { type: String, default: '确定' },
  /** MessageBox type: 'warning' | 'error' | 'info' */
  type: { type: String, default: 'warning' },
})

const emit = defineEmits(['confirm', 'cancel'])

async function handleClick() {
  try {
    await ElMessageBox.confirm(props.message, props.title, {
      confirmButtonText: props.confirmText,
      cancelButtonText: '取消',
      type: props.type,
    })
    emit('confirm')
  } catch {
    emit('cancel')
  }
}
</script>
