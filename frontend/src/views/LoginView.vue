<script setup>

import AppCard from "@/shared/components/AppCard.vue";
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'
import { IconUser, IconLock } from '@/shared/icons/index.js'

const POOL_KEY = 'auth_accounts'
const ACTIVE_KEY = 'auth_active'

function readPool() {
  try { return JSON.parse(localStorage.getItem(POOL_KEY) || '{}') } catch { return {} }
}
function loginToPool(username, access_token, refresh_token) {
  const pool = readPool()
  pool[username] = { access_token, refresh_token }
  localStorage.setItem(POOL_KEY, JSON.stringify(pool))
  sessionStorage.setItem(ACTIVE_KEY, username)
}

const router = useRouter()
const route = useRoute()

// ── Detect existing accounts ──
const existingActive = ref('')
const showSwitchPrompt = ref(false)

onMounted(() => {
  const pool = readPool()
  const names = Object.keys(pool)
  if (names.length > 0 && !route.query.add) {
    // Show first available account (this tab has no active yet)
    existingActive.value = names[0]
    showSwitchPrompt.value = true
  }
})

function onAddNewAccount() {
  showSwitchPrompt.value = false
  // Keep ?add in URL so refresh doesn't show prompt again
  router.replace({ query: { add: '1' } })
}

function onSwitchToExisting() {
  router.push('/dashboard')
}

// ── 登录表单 ──
const savedUser = localStorage.getItem('saved_username')
const loginUsername = ref(savedUser || '')
const loginPassword = ref('')
const rememberMe = ref(!!savedUser)

// ── 注册表单 ──
const regUsername = ref('')
const regPassword = ref('')
const regPassword2 = ref('')

// ── 公共状态 ──
const loading = ref(false)
const error = ref('')
const success = ref('')
const mode = ref('login') // 'login' | 'register'
const heroImageSrc = '/animal-assets/login-hero.jpg'
const heroImageVisible = ref(true)

// ── 注册表单校验 ──
const regErrors = computed(() => {
  const errs = {}
  if (mode.value !== 'register') return errs
  if (!regUsername.value.trim()) {
    errs.username = '请输入用户名'
  } else if (regUsername.value.trim().length < 3) {
    errs.username = '用户名至少 3 个字符'
  } else if (regUsername.value.trim().length > 20) {
    errs.username = '用户名最多 20 个字符'
  }
  if (!regPassword.value) {
    errs.password = '请输入密码'
  } else if (regPassword.value.length < 6) {
    errs.password = '密码至少 6 位'
  }
  if (!regPassword2.value) {
    errs.password2 = '请再次输入密码'
  } else if (regPassword.value !== regPassword2.value) {
    errs.password2 = '两次密码不一致'
  }
  return errs
})

const canRegister = computed(() => Object.keys(regErrors.value).length === 0)

async function handleLogin() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await axios.post('/api/ai/auth/login', {
      username: loginUsername.value,
      password: loginPassword.value,
    })
    if (data.ok) {
      loginToPool(loginUsername.value, data.access_token, data.refresh_token)
      if (rememberMe.value) {
        localStorage.setItem('saved_username', loginUsername.value)
      } else {
        localStorage.removeItem('saved_username')
      }
      router.push('/dashboard')
    } else {
      error.value = data.error || '登录失败'
    }
  } catch (e) {
    error.value = e.response?.data?.error || '服务异常，请检查后端是否启动'
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  if (!canRegister.value) {
    error.value = Object.values(regErrors.value)[0]
    return
  }
  loading.value = true
  error.value = ''
  try {
    const { data } = await axios.post('/api/ai/auth/register', {
      username: regUsername.value.trim(),
      password: regPassword.value,
    })
    if (data.ok) {
      loginToPool(regUsername.value.trim(), data.access_token, data.refresh_token)
      success.value = '注册成功，正在进入平台...'
      setTimeout(() => router.push('/dashboard'), 600)
    } else {
      error.value = data.error || '注册失败'
    }
  } catch (e) {
    error.value = e.response?.data?.error || '服务异常，请检查后端是否启动'
  } finally {
    loading.value = false
  }
}

function switchMode(m) {
  mode.value = m
  error.value = ''
  success.value = ''
}
</script>

<template>
  <div class="login-page">
    <!-- GPU 合成层背景 -->
    <div class="login-page__bg" aria-hidden="true"></div>

    <!-- 首页 Hero -->
    <div class="hero">
      <div class="hero__content">
        <!-- 左侧文案 -->
        <div class="hero__text">
          <div class="hero__title-row">
            <h1 class="hero-title">AI 自动化测试平台</h1>
            <span class="hero__version">v2.1</span>
          </div>

          <p class="hero__desc">
            <span class="hero__desc-line">AI 驱动的跨端 UI 自动化测试平台</span>
            <span class="hero__desc-line">让 Android / iOS 测试工作充满温暖质感</span>
          </p>

          <!-- ── 切换提示 ── -->
          <AppCard v-if="showSwitchPrompt" color="app-blue" pattern="app-blue" class="login-card">
            <div class="switch-prompt">
              <p class="switch-prompt__title">检测到已登录账号</p>
              <p class="switch-prompt__user">{{ existingActive }}</p>
              <div class="switch-prompt__actions">
                <el-button type="primary" size="large" block @click="onSwitchToExisting">
                  切换到 {{ existingActive }}
                </el-button>
                <el-button size="large" block @click="onAddNewAccount">
                  添加新账号
                </el-button>
              </div>
            </div>
          </AppCard>

          <!-- ── 登录卡片 ── -->
          <AppCard v-if="mode === 'login' && !showSwitchPrompt" color="app-blue" pattern="app-blue" class="login-card">
            <form class="login-form" @submit.prevent="handleLogin">
              <div class="form-field">
                <IconUser :size="18" class="form-icon" />
                <el-input
                  v-model="loginUsername"
                  placeholder="账号"
                  size="large"
                  
                  class="form-input"
                />
              </div>
              <div class="form-field">
                <IconLock :size="18" class="form-icon" />
                <el-input
                  v-model="loginPassword"
                  type="password"
                  show-password
                  placeholder="密码"
                  size="large"
                  class="form-input"
                />
              </div>

              <div class="form-remember">
                <el-switch v-model="rememberMe" size="small" />
                <span class="remember-label">记住账号</span>
              </div>

              <el-button
                type="primary"
                size="large"
                :loading="loading"
                block
                @click="handleLogin"
              >开始使用 →</el-button>
            </form>

            <p class="login-toggle" @click="switchMode('register')">
              没有账号？<span class="link">去注册 →</span>
            </p>
            <p v-if="error" class="login-error">{{ error }}</p>
          </AppCard>

          <!-- ── 注册卡片 ── -->
          <AppCard v-else-if="!showSwitchPrompt" color="app-teal" pattern="app-teal" class="login-card">
            <form class="login-form" @submit.prevent="handleRegister">
              <div class="form-field">
                <IconUser :size="18" class="form-icon" />
                <el-input
                  v-model="regUsername"
                  placeholder="设置账号（3-20 字符）"
                  size="large"
                  
                  class="form-input"
                />
              </div>
              <div class="form-field">
                <IconLock :size="18" class="form-icon" />
                <el-input
                  v-model="regPassword"
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
                  v-model="regPassword2"
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
                :disabled="!canRegister"
                block
                @click="handleRegister"
              >完成注册 →</el-button>
            </form>

            <p class="login-toggle" @click="switchMode('login')">
              已有账号？<span class="link">去登录 →</span>
            </p>
            <p v-if="error" class="login-error">{{ error }}</p>
            <p v-if="success" class="login-success">{{ success }}</p>
          </AppCard>
        </div>

        <!-- 右侧登录视觉图 -->
        <div class="hero__visual">
          <img
            v-if="heroImageVisible"
            :src="heroImageSrc"
            alt="AI 自动化测试平台视觉图"
            class="hero__animal"
            @error="heroImageVisible = false"
          />
        </div>
      </div>
    </div>

    <!-- 首页装饰 Footer -->
    <div class="login-footer">
      <span>AI Automated Testing Platform · Django + Vue + Animal Island</span>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  width: 100%;
  min-height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(circle at 16% 10%, var(--app-sky-cloud, rgba(255,255,255,0.82)), transparent 28%),
    radial-gradient(circle at 84% 18%, rgba(162,210,255,0.5), transparent 32%),
    radial-gradient(circle at 78% 90%, rgba(63,158,216,0.42), transparent 36%),
    radial-gradient(circle at 14% 88%, rgba(111,185,141,0.42), transparent 34%),
    linear-gradient(135deg, var(--app-sky, #dff5ff) 0%, var(--app-blue-light, #bde0fe) 38%, var(--app-ocean-soft, #a7d8ee) 68%, var(--app-forest-soft, #d6f2da) 100%);
  background-size: 180% 180%;
  animation: gradientBG 15s ease infinite;
  display: flex;
  flex-direction: column;
  position: relative;
  font-family: 'Quicksand', 'Inter', 'Microsoft YaHei', sans-serif;
}

/* Soft glass 背景光斑 */
.login-page__bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}

.login-page__bg::before,
.login-page__bg::after {
  content: '';
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.75;
  z-index: 0;
}

.login-page__bg::before {
  top: -120px;
  left: -100px;
  width: 400px;
  height: 400px;
  background: var(--app-sky-cloud, rgba(255,255,255,0.82));
}

.login-page__bg::after {
  right: -80px;
  bottom: -120px;
  width: 320px;
  height: 320px;
  background: var(--app-ocean, #3f9ed8);
}

.login-page::before {
  content: '';
  position: absolute;
  left: 10%;
  bottom: -110px;
  width: 360px;
  height: 300px;
  border-radius: 50%;
  background: var(--app-forest, #6fb98d);
  filter: blur(80px);
  opacity: 0.48;
  z-index: 0;
  pointer-events: none;
}

@keyframes gradientBG {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.login-page > .hero,
.login-page > .login-footer {
  position: relative;
  z-index: 1;
}

.hero {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 40px 40px;
}

.hero__content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 72px;
  align-items: end;
  max-width: 1020px;
  width: 100%;
  padding: 44px;
  border: 1px solid rgba(255, 255, 255, 0.55);
  border-radius: 30px;
  background: #fff;
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.07);
  background: #fff;
}

.hero__text {
  text-align: left;
}

.hero__title-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 16px;
}

.hero__version {
  flex-shrink: 0;
  display: inline-block;
  font-size: 12px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 999px;
  background: #fff;
  border: 1px solid rgba(255, 255, 255, 0.75);
  color: var(--ink);
  text-shadow: none;
  margin-top: 6px;
}

.hero__desc {
  font-size: 17px;
  color: #6b6070;
  line-height: 1.7;
  margin: 0 0 28px;
  max-width: 520px;
  text-shadow: 0 1px 0 rgba(255,255,255,0.4);
}

.hero__desc-line {
  display: block;
}

.hero__visual {
  display: flex;
  justify-content: center;
  width: 380px;
  justify-self: center;
}

.hero__animal {
  width: 380px;
  height: 280px;
  object-fit: cover;
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.72);
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.08);
}

/* Login/Register card */
.login-card {
  width: 380px;
  min-height: 280px;
  box-sizing: border-box;
  background: rgba(255, 255, 255, 0.52) !important;
  border: 1px solid rgba(255, 255, 255, 0.76) !important;
  border-radius: 24px !important;
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.08) !important;
  background: #fff;
}

/* Switch prompt */
.switch-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 8px 0;
  text-align: center;
}
.switch-prompt__title {
  font-size: 14px;
  color: #999;
  font-weight: 600;
  margin: 0;
}
.switch-prompt__user {
  font-size: 22px;
  color: var(--ink);
  font-weight: 800;
  margin: 0;
}
.switch-prompt__actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
  margin-top: 8px;
}

.login-card :deep(.el-card__body) {
  padding: 24px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.form-field {
  display: flex;
  align-items: center;
  gap: 10px;
}

.form-icon {
  color: #999;
  flex-shrink: 0;
}

.form-input {
  flex: 1;
}

.form-remember {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 2px;
}

.remember-label {
  font-size: 13px;
  color: #999;
  font-weight: 500;
  user-select: none;
}

.login-toggle {
  text-align: center;
  color: #999;
  cursor: pointer;
  font-size: 13px;
  margin: 16px 0 0;
  font-weight: 500;
}

.login-toggle:hover .link {
  text-decoration: underline;
}

.link {
  color: #5e9ed6;
  font-weight: 600;
}

.login-error {
  text-align: center;
  color: #e8998a;
  margin-top: 8px;
  font-size: 13px;
}

.login-success {
  text-align: center;
  color: var(--app-green-deep, #6fba2c);
  margin-top: 8px;
  font-size: 13px;
  font-weight: 600;
}

.login-footer {
  padding: 24px 40px;
  text-align: center;
  font-size: 12px;
  color: rgba(74, 78, 105, 0.72);
  text-shadow: 0 1px 0 rgba(255,255,255,0.45);
  opacity: 0.95;
}

@media (max-width: 768px) {
  .hero__content {
    grid-template-columns: 1fr;
    gap: 32px;
    padding: 28px 20px;
  }
  .hero__text { text-align: center; }
  .hero__title-row { justify-content: center; }
  .hero__desc { font-size: 14px; margin: 0 auto 24px; }
  .login-card { width: 100%; max-width: 360px; min-height: 0; margin: 0 auto; }
  .hero__visual { width: 100%; max-width: 360px; margin: 0 auto; }
  .hero__animal { width: 100%; max-width: 360px; height: 220px; }
}
</style>
