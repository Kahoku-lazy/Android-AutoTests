<script setup lang="ts">

import LoginErrorOverlay from '@/views/components/LoginErrorOverlay.vue'
import { useLoginView } from './LoginView.logic'
import AccountSwitchPrompt from '@/views/components/AccountSwitchPrompt.vue'
import LoginCard from '@/views/components/LoginCard.vue'
import RegisterCard from '@/views/components/RegisterCard.vue'

const {
  // ── 账号 & 视图状态 ──
  activeAccount,
  viewState,
  // ── 登录表单 ──
  loginUsername,
  loginPassword,
  rememberMe,
  loginErrors,
  canLogin,
  // ── 注册表单 ──
  regUsername,
  regPassword,
  regPassword2,
  regEmail,
  regErrors,
  canRegister,
  // ── 认证流程 ──
  loading,
  serverError,
  clearServerError,
  handleLogin,
  handleRegister,
  switchMode,
  // ── 账号切换 ──
  onSwitchToExisting,
  onAddNewAccount,
} = useLoginView()
</script>

<template>
  <div class="login-page" data-testid="login-page">
    <div class="login-page__bg" aria-hidden="true">
      <span class="login-page__glow login-page__glow--forest"></span>
    </div>

    <div class="hero">
      <div class="hero__content">
        <header class="hero__header">
          <div class="hero__title-row">
            <h1 class="hero-title">AI 自动化测试平台</h1>
            <span class="hero__version" aria-label="当前版本 v2.1">v2.1</span>
          </div>
          <p class="hero__desc">
            <span class="hero__desc-line">AI 自动化测试平台，让AI来做测试</span>
            <span class="hero__desc-line">让测试工作摆脱重复的劳动，专注于创造价值</span>
          </p>
        </header>

        <main class="hero__body">
          <LoginErrorOverlay
            :visible="!!serverError"
            :message="serverError"
            @close="clearServerError"
          />

          <AccountSwitchPrompt
            v-if="viewState === 'switchPrompt'"
            :existing-username="activeAccount"
            @switch-to="onSwitchToExisting"
            @add-new="onAddNewAccount"
          />

          <LoginCard
            v-else-if="viewState === 'login'"
            v-model:username="loginUsername"
            v-model:password="loginPassword"
            v-model:remember-me="rememberMe"
            :loading="loading"
            :errors="loginErrors"
            :can-submit="canLogin"
            @submit="handleLogin"
            @switch-to-register="switchMode('register')"
          />

          <RegisterCard
            v-else-if="viewState === 'register'"
            v-model:username="regUsername"
            v-model:email="regEmail"
            v-model:password="regPassword"
            v-model:password2="regPassword2"
            :loading="loading"
            :errors="regErrors"
            :can-submit="canRegister"
            @submit="handleRegister"
            @switch-to-login="switchMode('login')"
          />

          <aside class="hero__brand" aria-hidden="true">
            <span class="sticker sticker--ai sticker--featured">AI助手</span>
            <div class="hero__brand-tags">
              <span class="sticker sticker--device">设备管理</span>
              <span class="sticker sticker--case">用例编排</span>
              <span class="sticker sticker--runner">用例执行</span>
              <span class="sticker sticker--report">报告生成</span>
            </div>
          </aside>
        </main>
      </div>
    </div>

    <footer class="login-footer">
      <span>AI Automated Testing Platform · Django + Vue + Animal Island</span>
    </footer>
  </div>
</template>

<style src="./LoginView.style.css" scoped></style>
