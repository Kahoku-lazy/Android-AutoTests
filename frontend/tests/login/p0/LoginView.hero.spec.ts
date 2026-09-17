/**
 * [P0] 必测 — 登录页 hand-drawn Hero（CTA / Meeting 标题 / 无贴纸板）
 * 目录：tests/login/p0/
 */
import { ref, computed } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import LoginView from '@/views/LoginView.vue'
import { clearAuthStorage } from '../../helpers/mountComposable'

const viewState = ref<'login' | 'register' | 'switchPrompt'>('login')
const switchMode = vi.fn((m: 'login' | 'register' | 'switchPrompt') => {
  viewState.value = m
})

vi.mock('@/views/LoginView.logic', () => ({
  useLoginView: () => ({
    activeAccount: ref(''),
    viewState,
    loginUsername: ref(''),
    loginPassword: ref(''),
    rememberMe: ref(false),
    loginErrors: computed(() => ({})),
    canLogin: computed(() => false),
    regUsername: ref(''),
    regPassword: ref(''),
    regPassword2: ref(''),
    regEmail: ref(''),
    regErrors: computed(() => ({})),
    canRegister: computed(() => false),
    loading: ref(false),
    serverError: ref(''),
    clearServerError: vi.fn(),
    handleLogin: vi.fn(),
    handleRegister: vi.fn(),
    switchMode,
    onSwitchToExisting: vi.fn(),
    onAddNewAccount: vi.fn(),
  }),
}))

const stubs = {
  LoginCard: { template: '<div data-testid="stub-login-card">登录卡</div>' },
  RegisterCard: { template: '<div data-testid="stub-register-card">注册卡</div>' },
  AccountSwitchPrompt: { template: '<div data-testid="stub-switch-prompt">切换账号</div>' },
  LoginErrorOverlay: { template: '<div />', props: ['visible', 'message'] },
}

async function mountLogin() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: { template: '<div />' } },
      { path: '/login', component: { template: '<div />' } },
    ],
  })
  await router.push('/login')
  await router.isReady()
  return mount(LoginView, {
    global: { plugins: [router], stubs },
  })
}

describe('[P0] LoginView Hero', () => {
  beforeEach(() => {
    clearAuthStorage()
    viewState.value = 'login'
    switchMode.mockClear()
  })

  it('保留 login-page testid，且无动物贴纸板文案', async () => {
    const wrapper = await mountLogin()
    expect(wrapper.find('[data-testid="login-page"]').exists()).toBe(true)
    const text = wrapper.text()
    expect(text).not.toContain('设备管理')
    expect(text).not.toContain('用例编排')
    expect(text).not.toContain('用例执行')
    expect(text).not.toContain('报告生成')
    expect(text).toContain('AI 自动化测试平台')
  })

  it('默认 Meeting 标题为登录，并显示登录卡', async () => {
    const wrapper = await mountLogin()
    expect(wrapper.find('[data-testid="meeting-title"]').text()).toBe('登录')
    expect(wrapper.find('[data-testid="stub-login-card"]').exists()).toBe(true)
    expect(wrapper.find('.meeting-doodle .ac-card').exists()).toBe(false)
    expect(wrapper.find('.meeting-doodle .el-card').exists()).toBe(false)
  })

  it('点击注册 CTA：调用 switchMode(register) 并显示注册卡与标题', async () => {
    const wrapper = await mountLogin()
    await wrapper.find('[data-testid="login-mode-register"]').trigger('click')
    expect(switchMode).toHaveBeenCalledWith('register')
    await wrapper.vm.$nextTick()
    expect(wrapper.find('[data-testid="meeting-title"]').text()).toBe('注册')
    expect(wrapper.find('[data-testid="stub-register-card"]').exists()).toBe(true)
  })

  it('点击登录 CTA：回到登录卡', async () => {
    viewState.value = 'register'
    const wrapper = await mountLogin()
    await wrapper.find('[data-testid="login-mode-login"]').trigger('click')
    expect(switchMode).toHaveBeenCalledWith('login')
    await wrapper.vm.$nextTick()
    expect(wrapper.find('[data-testid="meeting-title"]').text()).toBe('登录')
    expect(wrapper.find('[data-testid="stub-login-card"]').exists()).toBe(true)
  })

  it('switchPrompt 态：隐藏模式 CTA，显示账号切换提示', async () => {
    viewState.value = 'switchPrompt'
    const wrapper = await mountLogin()
    expect(wrapper.find('[data-testid="login-mode-login"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="login-mode-register"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="stub-switch-prompt"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="meeting-title"]').text()).toBe('登录')
  })
})
