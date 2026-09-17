<script setup lang="ts">
/**
 * LoginErrorOverlay — 登录/注册错误浮层弹窗
 *
 * 覆盖层统一走 Element Plus（frontend/AGENTS.md「L5 覆盖层」口径）：遮罩、ESC、焦点与滚动锁
 * 由 el-dialog 提供；本组件只把「可见性 / 消息」映射到调用方状态，不再自建 backdrop。
 */
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
    @update:model-value="(v: boolean) => { if (!v) emit('close') }"
  >
    <p class="error-message" data-testid="login-error-message">{{ message }}</p>
    <template #footer>
      <el-button
        type="primary"
        data-testid="login-error-dismiss"
        @click="emit('close')"
      >
        知道了
      </el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.error-message {
  margin: 0;
  font-size: var(--app-size-sm);
  line-height: 1.6;
  color: var(--ink);
  word-break: break-word;
  max-height: min(40vh, 240px);
  overflow-y: auto;
}
</style>
