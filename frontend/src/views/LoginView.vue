<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { setToken } from '@/shared/api-client'
import { Button, Card, Input, Title, Switch } from 'animal-island-vue'
import { IconUser, IconLock } from '@/shared/icons/index.js'

const router = useRouter()

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
      setToken(data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      localStorage.setItem('username', loginUsername.value)
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
      setToken(data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      localStorage.setItem('username', regUsername.value.trim())
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
            <Title size="large" color="warm-peach-pink">AI 自动化测试平台</Title>
            <span class="hero__version">v2.1</span>
          </div>

          <p class="hero__desc">
            AI 驱动的跨端 UI 自动化测试平台
            <br />
            让 Android / iOS 测试工作充满温暖质感
          </p>

          <!-- ── 登录卡片 ── -->
          <Card v-if="mode === 'login'" color="warm-peach-pink" pattern="warm-peach-pink" class="login-card">
            <form class="login-form" @submit.prevent="handleLogin">
              <div class="form-field">
                <IconUser :size="18" class="form-icon" />
                <Input
                  v-model="loginUsername"
                  placeholder="账号"
                  size="large"
                  :shadow="false"
                  class="form-input"
                />
              </div>
              <div class="form-field">
                <IconLock :size="18" class="form-icon" />
                <Input
                  v-model="loginPassword"
                  type="password"
                  placeholder="密码"
                  size="large"
                  :shadow="false"
                  class="form-input"
                />
              </div>

              <div class="form-remember">
                <Switch v-model="rememberMe" size="small" />
                <span class="remember-label">记住账号</span>
              </div>

              <Button
                type="primary"
                size="large"
                :loading="loading"
                block
                @click="handleLogin"
              >开始使用 →</Button>
            </form>

            <p class="login-toggle" @click="switchMode('register')">
              没有账号？<span class="link">去注册 →</span>
            </p>
            <p v-if="error" class="login-error">{{ error }}</p>
          </Card>

          <!-- ── 注册卡片 ── -->
          <Card v-else color="app-teal" pattern="app-teal" class="login-card">
            <form class="login-form" @submit.prevent="handleRegister">
              <div class="form-field">
                <IconUser :size="18" class="form-icon" />
                <Input
                  v-model="regUsername"
                  placeholder="设置账号（3-20 字符）"
                  size="large"
                  :shadow="false"
                  class="form-input"
                />
              </div>
              <div class="form-field">
                <IconLock :size="18" class="form-icon" />
                <Input
                  v-model="regPassword"
                  type="password"
                  placeholder="设置密码（至少 6 位）"
                  size="large"
                  :shadow="false"
                  class="form-input"
                />
              </div>
              <div class="form-field">
                <IconLock :size="18" class="form-icon" />
                <Input
                  v-model="regPassword2"
                  type="password"
                  placeholder="确认密码"
                  size="large"
                  :shadow="false"
                  class="form-input"
                />
              </div>

              <Button
                type="primary"
                size="large"
                :loading="loading"
                :disabled="!canRegister"
                block
                @click="handleRegister"
              >完成注册 →</Button>
            </form>

            <p class="login-toggle" @click="switchMode('login')">
              已有账号？<span class="link">去登录 →</span>
            </p>
            <p v-if="error" class="login-error">{{ error }}</p>
            <p v-if="success" class="login-success">{{ success }}</p>
          </Card>
        </div>

        <!-- 右侧 Nook 图标 -->
        <div class="hero__visual">
          <img
            src="/animal-assets/animal_icon.png"
            alt="Animal Island"
            class="hero__animal"
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
  background: #7dc395;
  display: flex;
  flex-direction: column;
  position: relative;
}

/* GPU 合成层背景 */
.login-page__bg {
  position: absolute;
  inset: 0;
  background: url('/animal-assets/home_bg.webp') 0 0 / 400px auto repeat;
  will-change: transform;
  animation: bgScroll 80s linear infinite;
  z-index: 0;
}

@keyframes bgScroll {
  0%   { transform: translate3d(0, 0, 0); }
  100% { transform: translate3d(-400px, -400px, 0); }
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
  gap: 100px;
  align-items: center;
  max-width: 960px;
  width: 100%;
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
  padding: 2px 10px;
  border-radius: 10px;
  background: #e6f9f6;
  color: #19c8b9;
  text-shadow: none;
  margin-top: 6px;
}

.hero__desc {
  font-size: 17px;
  color: #7c5734;
  line-height: 1.7;
  margin: 0 0 28px;
  max-width: 520px;
  text-shadow: 0 1px 0 rgba(255,255,255,0.15);
}

.hero__visual {
  text-align: center;
}

.hero__animal {
  width: 320px;
  height: 200px;
  object-fit: contain;
  filter: drop-shadow(0 8px 20px rgba(0,0,0,0.15));
}

/* Login/Register card */
.login-card {
  width: 380px;
}

.login-card :deep(.animal-card-body) {
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
  color: var(--animal-text-color-secondary, #9f927d);
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
  color: var(--animal-text-color-secondary, #9f927d);
  font-weight: 500;
  user-select: none;
}

.login-toggle {
  text-align: center;
  color: var(--animal-text-color-secondary, #9f927d);
  cursor: pointer;
  font-size: 13px;
  margin: 16px 0 0;
  font-weight: 500;
}

.login-toggle:hover .link {
  text-decoration: underline;
}

.link {
  color: var(--animal-primary-color, #19c8b9);
  font-weight: 600;
}

.login-error {
  text-align: center;
  color: var(--animal-error-color, #e05a5a);
  margin-top: 8px;
  font-size: 13px;
}

.login-success {
  text-align: center;
  color: var(--animal-success-color, #6fba2c);
  margin-top: 8px;
  font-size: 13px;
  font-weight: 600;
}

.login-footer {
  padding: 24px 40px;
  text-align: center;
  font-size: 12px;
  color: #fff9e6;
  text-shadow: 0 1px 2px rgba(0,0,0,0.2);
  opacity: 0.85;
}

@media (max-width: 768px) {
  .hero__content {
    grid-template-columns: 1fr;
    gap: 32px;
  }
  .hero__text { text-align: center; }
  .hero__title-row { justify-content: center; }
  .hero__desc { font-size: 14px; margin: 0 auto 24px; }
  .login-card { width: 100%; max-width: 360px; margin: 0 auto; }
  .hero__animal { width: 200px; height: 124px; }
}
</style>
