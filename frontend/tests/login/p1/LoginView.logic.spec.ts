/**
 * [P1] 建议测 — LoginView.logic 编排层
 * 子 composable 已在 P0 覆盖；这里测编排独有行为（切模式清表单、提交前校验）。
 * 目录：tests/login/p1/
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ElMessage } from 'element-plus'
import { login } from '@/shared/api/auth'
import { useLoginView } from '@/views/LoginView.logic'
import { clearAuthStorage, mountComposable } from '../../helpers/mountComposable'

vi.mock('@/shared/api/auth', () => ({
  login: vi.fn(),
  register: vi.fn(),
}))

vi.mock('element-plus', () => ({
  ElMessage: { warning: vi.fn(), success: vi.fn() },
}))

describe('[P1] useLoginView（编排）', () => {
  beforeEach(() => {
    clearAuthStorage()
    vi.clearAllMocks()
  })

  it('切到 register 时：清空注册表单字段', async () => {
    const { result } = await mountComposable(() => useLoginView())
    result.regUsername.value = 'bob'
    result.regPassword.value = '123456'
    result.regPassword2.value = '123456'
    result.regEmail.value = 'bob@example.com'

    result.switchMode('register')

    expect(result.regUsername.value).toBe('')
    expect(result.regPassword.value).toBe('')
    expect(result.regPassword2.value).toBe('')
    expect(result.regEmail.value).toBe('')
    expect(result.viewState.value).toBe('register')
  })

  it('切到 login 时：清空登录密码（保留用户名）', async () => {
    const { result } = await mountComposable(() => useLoginView())
    result.loginUsername.value = 'alice'
    result.loginPassword.value = 'secret'

    result.switchMode('login')

    expect(result.loginUsername.value).toBe('alice')
    expect(result.loginPassword.value).toBe('')
    expect(result.viewState.value).toBe('login')
  })

  it('登录表单无效时：只警告，不调 API', async () => {
    const { result } = await mountComposable(() => useLoginView())
    result.loginUsername.value = ''
    result.loginPassword.value = ''

    await result.handleLogin()

    expect(ElMessage.warning).toHaveBeenCalled()
    expect(login).not.toHaveBeenCalled()
  })
})
