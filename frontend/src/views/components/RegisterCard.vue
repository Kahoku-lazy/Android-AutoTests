<script setup lang="ts">
import AppCard from '@/shared/components/AppCard.vue'
import { IconUser, IconLock, IconMail } from '@/shared/icons/index'
import type { FieldErrors } from '@/shared/types/auth'

export interface RegisterCardProps {
  username: string
  email: string
  password: string
  password2: string
  loading?: boolean
  errors: FieldErrors
  canSubmit: boolean
}

withDefaults(defineProps<RegisterCardProps>(), {
  loading: false,
})

const emit = defineEmits<{
  'update:username': [value: string]
  'update:email': [value: string]
  'update:password': [value: string]
  'update:password2': [value: string]
  submit: []
  switchToLogin: []
}>()
</script>

<template>
  <AppCard color="app-teal" class="login-card">
    <form class="auth-form" @submit.prevent="emit('submit')">
      <div class="form-field" data-testid="register-username">
        <IconUser :size="18" class="form-icon" />
        <el-input
          :model-value="username"
          @update:model-value="emit('update:username', $event)"
          placeholder="设置账号（3-20 字符）"
          size="large"
          class="form-input"
          :class="{ 'is-error': errors.username }"
        />
      </div>
      <p v-if="errors.username" class="field-error">{{ errors.username }}</p>

      <div class="form-field" data-testid="register-email">
        <IconMail :size="18" class="form-icon" />
        <el-input
          :model-value="email"
          @update:model-value="emit('update:email', $event)"
          placeholder="邮箱地址"
          size="large"
          class="form-input"
          :class="{ 'is-error': errors.email }"
        />
      </div>
      <p v-if="errors.email" class="field-error">{{ errors.email }}</p>

      <div class="form-field" data-testid="register-password">
        <IconLock :size="18" class="form-icon" />
        <el-input
          :model-value="password"
          @update:model-value="emit('update:password', $event)"
          type="password"
          show-password
          placeholder="设置密码（至少 6 位）"
          size="large"
          class="form-input"
          :class="{ 'is-error': errors.password }"
        />
      </div>
      <p v-if="errors.password" class="field-error">{{ errors.password }}</p>

      <div class="form-field" data-testid="register-password2">
        <IconLock :size="18" class="form-icon" />
        <el-input
          :model-value="password2"
          @update:model-value="emit('update:password2', $event)"
          type="password"
          show-password
          placeholder="确认密码"
          size="large"
          class="form-input"
          :class="{ 'is-error': errors.password2 }"
        />
      </div>
      <p v-if="errors.password2" class="field-error">{{ errors.password2 }}</p>

      <div class="form-submit" data-testid="register-submit">
        <el-button
          type="primary"
          size="large"
          :loading="loading"
          :disabled="!canSubmit"
          @click="emit('submit')"
        >完成注册 →</el-button>
      </div>
    </form>

    <button class="form-toggle" data-testid="register-to-login" @click="emit('switchToLogin')">
      已有账号？<span class="form-link">去登录 →</span>
    </button>
  </AppCard>
</template>

<style>
@import '@/views/shared/login-card.css';
@import '@/views/shared/auth-form-card.css';
</style>
