<script setup lang="ts">
import AppCard from '@/shared/components/AppCard.vue'

interface Props {
  existingUsername: string
}

defineProps<Props>()

const emit = defineEmits<{
  switchTo: []
  addNew: []
}>()
</script>

<template>
  <AppCard color="app-blue" class="login-card">
    <div class="switch-prompt">
      <p class="switch-prompt__title">检测到已登录账号</p>
      <p class="switch-prompt__user">{{ existingUsername }}</p>
      <div class="switch-prompt__actions">
        <el-button type="primary" size="large" block @click="emit('switchTo')">
          切换到 {{ existingUsername }}
        </el-button>
        <el-button size="large" block @click="emit('addNew')">
          添加新账号
        </el-button>
      </div>
    </div>
  </AppCard>
</template>

<style scoped>
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
