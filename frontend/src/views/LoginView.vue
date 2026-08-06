<script setup lang="ts">
import LoginErrorOverlay from '@/views/components/LoginErrorOverlay.vue'
import { useLoginView } from './LoginView.logic'
import AccountSwitchPrompt from '@/views/components/AccountSwitchPrompt.vue'
import LoginCard from '@/views/components/LoginCard.vue'
import RegisterCard from '@/views/components/RegisterCard.vue'

const {
  activeAccount,
  viewState,
  loginUsername,
  loginPassword,
  rememberMe,
  regUsername,
  regPassword,
  regPassword2,
  regEmail,
  loading,
  loginErrors,
  canLogin,
  regErrors,
  canRegister,
  heroImageSrc,
  heroImageVisible,
  serverError,
  clearServerError,
  handleLogin,
  handleRegister,
  switchMode,
  onSwitchToExisting,
  onAddNewAccount,
  onHeroImageError,
} = useLoginView()
</script>

<template>
  <div class="login-page">
    <div class="login-page__bg" aria-hidden="true"></div>

    <div class="hero">
      <div class="hero__content">
        <div class="hero__header">
          <div class="hero__title-row">
            <h1 class="hero-title">AI 自动化测试平台</h1>
            <span class="hero__version">v2.1</span>
          </div>
          <p class="hero__desc">
            <span class="hero__desc-line">AI 自动化测试平台，让AI来做测试</span>
            <span class="hero__desc-line">让测试工作摆脱重复的劳动，专注于创造价值</span>
          </p>
        </div>

        <div class="hero__body">
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

          <div class="hero__visual">
            <img
              v-if="heroImageVisible"
              :src="heroImageSrc"
              alt="AI 自动化测试平台视觉图"
              class="hero__animal"
              @error="onHeroImageError"
            />
          </div>
        </div>
      </div>
    </div>

    <div class="login-footer">
      <span>AI Automated Testing Platform · Django + Vue + Animal Island</span>
    </div>
  </div>
</template>

<style src="./LoginView.style.css" scoped></style>
