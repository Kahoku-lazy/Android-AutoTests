<script setup lang="ts">
import { computed } from "vue"

import LoginErrorOverlay from "@/views/components/LoginErrorOverlay.vue"
import { useLoginView } from "./LoginView.logic"
import LoginCard from "@/views/components/LoginCard.vue"
import RegisterCard from "@/views/components/RegisterCard.vue"

const {
  // ── 视图状态 ──
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
} = useLoginView()

/** Meeting doodle 标题：登录 / 注册 */
const meetingTitle = computed(() => (viewState.value === "register" ? "注册" : "登录"))
</script>

<template>
  <div class="login-page" data-testid="login-page">
    <div class="login-page__doodles" aria-hidden="true">
      <svg
        class="login-doodle login-doodle--swirl"
        width="32"
        height="32"
        viewBox="0 0 32 32"
        fill="none"
      >
        <path
          d="M16 16 Q16 10 22 10 Q28 10 28 16 Q28 24 20 24 Q10 24 10 14 Q10 6 20 6 Q30 6 30 16"
          stroke="var(--ink)"
          stroke-width="2"
          stroke-linecap="round"
          opacity="0.28"
        />
      </svg>
      <svg
        class="login-doodle login-doodle--ring"
        width="56"
        height="56"
        viewBox="0 0 60 60"
        fill="none"
      >
        <circle
          cx="30"
          cy="30"
          r="28"
          stroke="var(--comp-paper-mark-brown)"
          stroke-width="6"
          fill="none"
          opacity="0.12"
        />
        <circle
          cx="30"
          cy="30"
          r="22"
          stroke="var(--comp-paper-mark-brown)"
          stroke-width="1.5"
          fill="none"
          opacity="0.12"
        />
      </svg>
      <svg
        class="login-doodle login-doodle--star-a"
        width="14"
        height="14"
        viewBox="0 0 24 24"
        fill="none"
      >
        <path
          d="M12 2 L13.5 9 L20 9 L14.5 13.5 L16.5 20.5 L12 16.5 L7.5 20.5 L9.5 13.5 L4 9 L10.5 9 Z"
          fill="var(--comp-paper-mark-yellow)"
          stroke="var(--comp-paper-mark-yellow)"
          stroke-width="1"
          stroke-linejoin="round"
        />
      </svg>
      <svg
        class="login-doodle login-doodle--star-b"
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
      >
        <path
          d="M12 2 L13.5 9 L20 9 L14.5 13.5 L16.5 20.5 L12 16.5 L7.5 20.5 L9.5 13.5 L4 9 L10.5 9 Z"
          fill="var(--comp-paper-mark-red)"
          stroke="var(--comp-paper-mark-red)"
          stroke-width="1"
          stroke-linejoin="round"
        />
      </svg>
    </div>

    <div class="hero">
      <div class="hero__intro">
        <header class="hero__header">
          <div class="hero__title-row">
            <h1 class="hero-title">AI 自动化测试平台</h1>
            <span class="hero__version" aria-label="当前版本 v3.0">v3.0</span>
          </div>
          <p class="hero__tagline">实现让AI来做测试</p>
          <p class="hero__tagline">让测试工作摆脱重复的劳动</p>
          <p class="hero__tagline">专注于创造价值</p>
        </header>

        <div class="hero__cta" role="group" aria-label="登录或注册">
          <button
            type="button"
            class="hero-cta hero-cta--primary"
            :class="{ 'is-active': viewState === 'login' }"
            data-testid="login-mode-login"
            :aria-pressed="viewState === 'login'"
            @click="switchMode('login')"
          >
            登录
          </button>
          <button
            type="button"
            class="hero-cta hero-cta--ghost"
            :class="{ 'is-active': viewState === 'register' }"
            data-testid="login-mode-register"
            :aria-pressed="viewState === 'register'"
            @click="switchMode('register')"
          >
            注册 →
          </button>
        </div>
      </div>

      <div class="hero-sketch">
        <div class="meeting-doodle" data-testid="meeting-doodle">
          <div class="meeting-doodle__tape" aria-hidden="true"></div>
          <h2 class="meeting-doodle__title" data-testid="meeting-title">{{ meetingTitle }}</h2>
          <div class="meeting-doodle__lines" aria-hidden="true">
            <span class="doodle-line"></span>
            <span class="doodle-line doodle-line--teal"></span>
            <span class="doodle-line doodle-line--short"></span>
            <span class="doodle-line doodle-line--red"></span>
          </div>

          <div class="meeting-doodle__body">
            <LoginErrorOverlay
              :visible="!!serverError"
              :message="serverError"
              @close="clearServerError"
            />

            <LoginCard
              v-if="viewState === 'login'"
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
          </div>
        </div>
      </div>
    </div>

    <footer class="login-footer">
      <span>AI Automated Testing Platform · Django + Vue + Animal Island</span>
    </footer>
  </div>
</template>

<style src="./LoginView.style.css" scoped></style>
