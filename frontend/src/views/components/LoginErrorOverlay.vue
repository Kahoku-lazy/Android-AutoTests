<!--
LoginErrorOverlay — 登录页服务端错误提示（L5 覆盖层）

职责：纯展示。文案和开关都由父级 LoginView 持有：
serverError 有内容则打开，关闭后把清错交给父级。

契约：
- message: 原样展示的错误文案
- visible: 对话框是否打开（受控，组件内不改这个值）
- emit close: 无载荷。对话框关掉，或点「知道了」时发出

交互：
- el-dialog 且 append-to-body，盖在登录/注册表单之上
- 只在 model-value 变为 false 时 emit；打开时不发
- 蒙层、标题栏关闭、「知道了」都收成同一次 close

展示：
- 文案颜色 --ink，字号 --app-size-sm
- 超长文案在 min(40vh, 240px) 内换行滚动
- data-testid：login-error-message、login-error-dismiss
-->

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
  line-height: 1.6;
  color: var(--ink);
  word-break: break-word;
  max-height: min(40vh, 240px);
  overflow-y: auto;
}
</style>
