<script setup lang="ts">
/**
 * LoginErrorOverlay — 登录/注册错误浮层弹窗
 *
 * 覆盖层统一走 Element Plus（frontend/AGENTS.md「L5 覆盖层」口径）：遮罩、ESC、焦点与滚动锁
 * 由 el-dialog 提供；本组件只把「可见性 / 消息」映射到调用方状态，不再自建 backdrop。
 *
 * append-to-body 是必需的（见 frontend-l5-overlay「Blocking overlays escape transformed ancestors」）：
 * 挂载点 .meeting-doodle 带 transform: rotate(1.2deg)，而带 transform 的祖先会成为
 * position: fixed 后代的包含块 —— 不 Teleport 到 body，遮罩就只盖住那张便签卡（实测 424×403）。
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
  line-height: 1.6;
  color: var(--ink);
  word-break: break-word;
  max-height: min(40vh, 240px);
  overflow-y: auto;
}
</style>
