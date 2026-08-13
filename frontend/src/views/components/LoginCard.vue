<script setup lang="ts">
import AppCard from '@/shared/components/AppCard.vue'
import { IconUser, IconLock } from '@/shared/icons/index'
import type { FieldErrors } from '@/shared/types/auth'

export interface LoginCardProps {
  username: string
  password: string
  rememberMe?: boolean
  loading?: boolean
  errors: FieldErrors
  canSubmit: boolean
}

withDefaults(defineProps<LoginCardProps>(), {
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
    <form class="auth-form" @submit.prevent="emit('submit')">
      <!-- testid 挂在原生包裹层：Element Plus 组件不一定透传 data-testid -->
      <div class="form-field" data-testid="login-username">
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

      <div class="form-field" data-testid="login-password">
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

      <div class="form-remember" data-testid="login-remember">
        <el-switch
          :model-value="rememberMe"
          @update:model-value="emit('update:rememberMe', !!$event)"
          size="small"
        />
        <span class="remember-label">记住账号</span>
      </div>

      <div class="form-submit" data-testid="login-submit">
        <el-button
          type="primary"
          size="large"
          :loading="loading"
          :disabled="!canSubmit"
          @click="emit('submit')"
        >登录</el-button>
      </div>
    </form>

    <button class="form-toggle" data-testid="login-to-register" @click="emit('switchToRegister')">
      没有账号？<span class="form-link">去注册 →</span>
    </button>
  </AppCard>
</template>

<style>
@import '@/views/shared/login-card.css';
@import '@/views/shared/auth-form-card.css';
</style>
