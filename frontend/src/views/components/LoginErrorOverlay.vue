<script setup lang="ts">
defineProps<{
  message: string
  visible: boolean
}>()

const emit = defineEmits<{
  close: []
}>()
</script>

<template>
  <el-dialog
    :model-value="visible"
    title="提示"
    width="420px"
    append-to-body
    @update:model-value="
      (v: boolean) => {
        if (!v) emit('close')
      }
    "
  >
    <p class="error-message" data-testid="login-error-message">{{ message }}</p>
    <template #footer>
      <el-button type="primary" data-testid="login-error-dismiss" @click="emit('close')">
        知道了
      </el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.error-message {
  margin: 0;
  font-size: var(--app-size-sm);
  line-height: var(--app-line-height-relaxed);
  color: var(--app-text-primary);
  word-break: break-word;
  max-height: min(40vh, 240px);
  overflow-y: auto;
}
</style>
