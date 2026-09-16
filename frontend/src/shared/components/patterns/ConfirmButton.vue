<template>
  <!-- doodle：涂鸦危险按钮外观；默认仍走 el-button -->
  <DoodleBtn
    v-if="doodle"
    tone="danger"
    :disabled="disabled"
    @click.stop="handleClick"
  >
    <slot />
  </DoodleBtn>
  <el-button v-else v-bind="$attrs" :disabled="disabled" @click.stop="handleClick">
    <slot />
  </el-button>
</template>

<script setup>
import { ElMessageBox } from 'element-plus'
import DoodleBtn from '@/shared/components/DoodleBtn.vue'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  /** Confirmation message shown in the dialog */
  message: { type: String, required: true },
  /** Dialog title */
  title: { type: String, default: '确认操作' },
  /** Text for the confirm button */
  confirmText: { type: String, default: '确定' },
  /** MessageBox type: 'warning' | 'error' | 'info' */
  type: { type: String, default: 'warning' },
  /** 使用 DoodleBtn danger 外观（任务卡删除等） */
  doodle: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['confirm', 'cancel'])

async function handleClick() {
  if (props.disabled) return
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
