<script setup lang="ts">
import AppCard from '@/shared/components/AppCard.vue'
import { IconUser, IconPlus } from '@/shared/icons/index'

export interface AccountSwitchPromptProps {
  existingUsername: string
}

defineProps<AccountSwitchPromptProps>()

const emit = defineEmits<{
  switchTo: []
  addNew: []
}>()
</script>

<template>
  <AppCard color="app-blue" class="login-card" data-testid="account-switch-prompt">
    <div class="switch-prompt">
      <p class="switch-prompt__title">检测到已登录账号</p>
      <p class="switch-prompt__user">{{ existingUsername }}</p>
      <div class="switch-prompt__actions">
        <div data-testid="switch-to-existing">
          <el-button type="primary" size="large" block @click="emit('switchTo')">
            <IconUser :size="16" />
            <span>切换到 {{ existingUsername }}</span>
          </el-button>
        </div>
        <div data-testid="add-new-account">
          <el-button size="large" block @click="emit('addNew')">
            <IconPlus :size="16" />
            <span>添加新账号</span>
          </el-button>
        </div>
      </div>
    </div>
  </AppCard>
</template>

<style scoped>
/* ── 内容 ── */
.switch-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--app-space-md);
  padding: var(--app-space-sm) 0;
  text-align: center;
}
.switch-prompt__title {
  font-size: var(--app-size-sm);
  color: var(--app-text-secondary);
  font-weight: 600;
  margin: 0;
}
.switch-prompt__user {
  font-size: var(--app-size-xl);
  color: var(--ink);
  font-weight: 800;
  margin: 0;
}
.switch-prompt__actions {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-sm);
  width: 100%;
  margin-top: 8px;
}

</style>
<style>
@import '@/views/shared/login-card.css';
</style>
