<script setup lang="ts">
/**
 * LoginErrorOverlay — 登录/注册错误浮层弹窗
 *
 * 替代原内联 ErrorState，固定定位悬浮在登录页面之上，
 * 不破坏 hero 布局。支持点击遮罩/按钮/ESC 关闭。
 */
import { watch, onBeforeUnmount } from 'vue'

const props = defineProps<{
  message: string
  visible: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('close')
}

watch(
  () => props.visible,
  (visible) => {
    if (visible) {
      document.addEventListener('keydown', onKeydown)
    } else {
      document.removeEventListener('keydown', onKeydown)
    }
  },
  { immediate: true },
)

onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))
</script>

<template>
  <Teleport to="body">
    <Transition name="overlay">
      <div
        v-if="visible"
        class="error-overlay"
        data-testid="login-error-overlay"
        @click.self="emit('close')"
      >
        <div class="error-card">
          <div class="error-card__icon">!</div>
          <p class="error-card__message" data-testid="login-error-message">{{ message }}</p>
          <button
            class="error-card__btn"
            data-testid="login-error-dismiss"
            @click="emit('close')"
          >知道了</button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.error-overlay {
  position: fixed;
  inset: 0;
  /* 浮于登录页 hero/表单之上 */
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--app-overlay);
  padding: 20px;
}

.error-card {
  background: var(--paper, #fefcf5);
  border: 2.5px solid var(--ink);
  border-radius: var(--app-radius-lg);
  box-shadow: var(--app-shadow-lg);
  max-width: 400px;
  width: 100%;
  max-height: min(80vh, 480px);
  padding: var(--app-space-xl) 28px var(--app-space-lg);
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--app-space-md);
  overflow: hidden;
}

.error-card__icon {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--app-status-danger, #FFB5A7);
  color: var(--paper);
  font-size: var(--app-size-xl);
  font-weight: 800;
  font-family: var(--app-font);
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  flex-shrink: 0;
}

.error-card__message {
  margin: 0;
  font-size: var(--app-size-sm);
  font-family: var(--app-font);
  color: var(--ink);
  line-height: 1.6;
  word-break: break-word;
  max-height: min(40vh, 240px);
  overflow-y: auto;
  min-height: 0;
  width: 100%;
}

.error-card__btn {
  margin-top: var(--app-space-xs);
  padding: var(--app-space-sm) 28px;
  font-size: var(--app-size-xs);
  font-weight: 700;
  font-family: var(--app-font);
  color: var(--ink);
  background: var(--app-highlight, #FFE066);
  border: 2px solid var(--ink);
  border-radius: var(--app-radius-sm);
  cursor: pointer;
  transition: transform 0.12s var(--app-ease);
  flex-shrink: 0;
}

.error-card__btn:hover {
  transform: translate(1px, 1px);
}

.error-card__btn:active {
  transform: translate(2px, 2px);
}

/* ── 入场/退场动画 ── */
.overlay-enter-active {
  transition: opacity 0.2s ease;
}
.overlay-enter-active .error-card {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.overlay-leave-active {
  transition: opacity 0.15s ease;
}
.overlay-leave-active .error-card {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.overlay-enter-from {
  opacity: 0;
}
.overlay-enter-from .error-card {
  opacity: 0;
  transform: scale(0.92) translateY(8px);
}
.overlay-leave-to {
  opacity: 0;
}
.overlay-leave-to .error-card {
  opacity: 0;
  transform: scale(0.95);
}
</style>
