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

const viewState = ref<'login' | 'register'>('login')
const switchMode = vi.fn((m: 'login' | 'register') => {
  viewState.value = m
})

vi.mock('@/views/LoginView.logic', () => ({
  useLoginView: () => ({
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
  }),
}))

const stubs = {
  LoginCard: { template: '<div data-testid="stub-login-card">登录卡</div>' },
  RegisterCard: { template: '<div data-testid="stub-register-card">注册卡</div>' },
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

  it('左栏呈现四行品牌文案与 v3.0 版本徽标', async () => {
    const wrapper = await mountLogin()
    expect(wrapper.find('.hero-title').text()).toBe('AI 自动化测试平台')
    expect(wrapper.findAll('.hero__tagline').map((el) => el.text())).toEqual([
      '实现让AI来做测试',
      '让测试工作摆脱重复的劳动',
      '专注于创造价值',
    ])
    expect(wrapper.find('.hero__version').text()).toBe('v3.0')
    // 眉标整块已移除：左栏不再有独立成行的「AI 自动化测试」
    expect(wrapper.find('.hero__eyebrow').exists()).toBe(false)
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

  it('两个模式 CTA 恒可见，且不再有账号切换提示', async () => {
    const wrapper = await mountLogin()
    expect(wrapper.find('[data-testid="login-mode-login"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="login-mode-register"]').exists()).toBe(true)
    // 登录页只有 login / register 两态：切换提示卡的内容不应再出现
    expect(wrapper.text()).not.toContain('检测到已登录账号')
    expect(wrapper.text()).not.toContain('添加新账号')

    viewState.value = 'register'
    await wrapper.vm.$nextTick()
    expect(wrapper.find('[data-testid="login-mode-login"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="login-mode-register"]').exists()).toBe(true)
  })
})
