<template>
  <DoodleBtn v-if="doodle" tone="danger" :disabled="disabled" @click.stop="handleClick">
    <slot />
  </DoodleBtn>
  <el-button v-else v-bind="$attrs" :disabled="disabled" @click.stop="handleClick">
    <slot />
  </el-button>
</template>

<script setup>
import { ElMessageBox } from "element-plus"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"

defineOptions({ inheritAttrs: false })

const props = defineProps({
  message: { type: String, required: true },

  title: { type: String, default: "确认操作" },

  confirmText: { type: String, default: "确定" },

  type: { type: String, default: "warning" },

  doodle: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(["confirm", "cancel"])

async function handleClick() {
  if (props.disabled) return
  try {
    await ElMessageBox.confirm(props.message, props.title, {
      confirmButtonText: props.confirmText,
      cancelButtonText: "取消",
      type: props.type,
    })
    emit("confirm")
  } catch {
    emit("cancel")
  }
}
</script>
