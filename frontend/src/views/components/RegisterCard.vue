<script setup lang="ts">
import AppCard from '@/shared/components/AppCard.vue'
import { IconUser, IconLock } from '@/shared/icons/index.js'
import type { FieldErrors } from '@/shared/types/auth'

interface Props {
  username: string
  password: string
  password2: string
  loading?: boolean
  errors: FieldErrors
  canSubmit: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
})

const emit = defineEmits<{
  'update:username': [value: string]
  'update:password': [value: string]
  'update:password2': [value: string]
  submit: []
  switchToLogin: []
}>()
</script>

<template>
  <AppCard color="app-teal" class="login-card">
    <form class="login-form" @submit.prevent="emit('submit')">
      <div class="form-field">
        <IconUser :size="18" class="form-icon" />
        <el-input
          :model-value="username"
          @update:model-value="emit('update:username', $event)"
          placeholder="设置账号（3-20 字符）"
          size="large"
          class="form-input"
        />
      </div>
      <div class="form-field">
        <IconLock :size="18" class="form-icon" />
        <el-input
          :model-value="password"
          @update:model-value="emit('update:password', $event)"
          type="password"
          show-password
          placeholder="设置密码（至少 6 位）"
          size="large"
          class="form-input"
        />
      </div>
      <div class="form-field">
        <IconLock :size="18" class="form-icon" />
        <el-input
          :model-value="password2"
          @update:model-value="emit('update:password2', $event)"
          type="password"
          show-password
          placeholder="确认密码"
          size="large"
          class="form-input"
        />
      </div>

      <el-button
        type="primary"
        size="large"
        :loading="loading"
        :disabled="!canSubmit"
        block
        @click="emit('submit')"
      >完成注册 →</el-button>
    </form>

    <p class="login-toggle" @click="emit('switchToLogin')">
      已有账号？<span class="link">去登录 →</span>
    </p>
  </AppCard>
</template>

<style>
@import '@/views/shared/login-form.css';
</style>
