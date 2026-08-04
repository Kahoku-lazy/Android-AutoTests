<script setup lang="ts">
import AppCard from '@/shared/components/AppCard.vue'
import { IconUser, IconLock } from '@/shared/icons/index.js'
import type { FieldErrors } from '@/shared/types/auth'

interface Props {
  username: string
  password: string
  rememberMe?: boolean
  loading?: boolean
  errors: FieldErrors
  canSubmit: boolean
}

const props = withDefaults(defineProps<Props>(), {
  rememberMe: false,
  loading: false,
})

const emit = defineEmits<{
  'update:username': [value: string]
  'update:password': [value: string]
  'update:rememberMe': [value: boolean]
  submit: []
  switchToRegister: []
}>()
</script>

<template>
  <AppCard color="app-blue" class="login-card">
    <form class="login-form" @submit.prevent="emit('submit')">
      <div class="form-field">
        <IconUser :size="18" class="form-icon" />
        <el-input
          :model-value="username"
          @update:model-value="emit('update:username', $event)"
          placeholder="账号"
          size="large"
          class="form-input"
          :class="{ 'is-error': errors.username }"
        />
      </div>
      <p v-if="errors.username" class="field-error">{{ errors.username }}</p>

      <div class="form-field">
        <IconLock :size="18" class="form-icon" />
        <el-input
          :model-value="password"
          @update:model-value="emit('update:password', $event)"
          type="password"
          show-password
          placeholder="密码"
          size="large"
          class="form-input"
          :class="{ 'is-error': errors.password }"
        />
      </div>
      <p v-if="errors.password" class="field-error">{{ errors.password }}</p>

      <div class="form-remember">
        <el-switch :model-value="rememberMe" @update:model-value="emit('update:rememberMe', !!$event)" size="small" />
        <span class="remember-label">记住账号</span>
      </div>

      <el-button
        type="primary"
        size="large"
        :loading="loading"
        :disabled="!canSubmit"
        block
        @click="emit('submit')"
      >登录</el-button>
    </form>

    <p class="login-toggle" @click="emit('switchToRegister')">
      没有账号？<span class="link">去注册 →</span>
    </p>
  </AppCard>
</template>

<style>
@import '@/views/shared/login-form.css';
</style>

<style scoped>
.field-error {
  margin: -8px 0 0 28px;
  font-size: var(--app-size-xs);
  color: var(--app-error);
  font-weight: 500;
}

.form-remember {
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
  padding: 0 2px;
}

.remember-label {
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
  font-weight: 500;
  user-select: none;
}
</style>
