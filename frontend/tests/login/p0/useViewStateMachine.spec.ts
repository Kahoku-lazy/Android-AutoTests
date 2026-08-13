/**
 * [P0] 必测 — 登录页三态视图切换
 * 目录：tests/login/p0/
 */
/**
 * [P0] 必测 — 登录页三态视图切换
 * 目录：tests/login/p0/
 */
import { computed } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useViewStateMachine } from '@/views/composables/useViewStateMachine'
import { clearAuthStorage, mountComposable } from '../../helpers/mountComposable'

describe('[P0] useViewStateMachine', () => {
  beforeEach(() => {
    clearAuthStorage()
  })

  it('无已登录账号时，初始保持 login', async () => {
    const clearError = vi.fn()
    const { result } = await mountComposable(() =>
      useViewStateMachine(computed(() => []), clearError),
    )
    expect(result.viewState.value).toBe('login')
  })

  it('有已登录账号且无 add 参数时，进入 switchPrompt', async () => {
    const clearError = vi.fn()
    const { result } = await mountComposable(() =>
      useViewStateMachine(computed(() => ['alice']), clearError),
    )
    expect(result.viewState.value).toBe('switchPrompt')
  })

  it('有账号但 query.add=1 时，仍保持 login', async () => {
    const clearError = vi.fn()
    const { result } = await mountComposable(
      () => useViewStateMachine(computed(() => ['alice']), clearError),
      { initialQuery: { add: '1' } },
    )
    expect(result.viewState.value).toBe('login')
  })

  it('switchMode 会清错并切换视图', async () => {
    const clearError = vi.fn()
    const { result } = await mountComposable(() =>
      useViewStateMachine(computed(() => []), clearError),
    )
    result.switchMode('register')
    expect(clearError).toHaveBeenCalled()
    expect(result.viewState.value).toBe('register')
  })

  it('onSwitchToExisting 跳转 dashboard', async () => {
    const clearError = vi.fn()
    const { result, router } = await mountComposable(() =>
      useViewStateMachine(computed(() => ['alice']), clearError),
    )
    const push = vi.spyOn(router, 'push')
    result.onSwitchToExisting()
    expect(push).toHaveBeenCalledWith('/dashboard')
  })

  it('onAddNewAccount 切到 login 并写入 query.add', async () => {
    const clearError = vi.fn()
    const { result, router } = await mountComposable(() =>
      useViewStateMachine(computed(() => ['alice']), clearError),
    )
    const replace = vi.spyOn(router, 'replace')
    result.onAddNewAccount()
    expect(clearError).toHaveBeenCalled()
    expect(result.viewState.value).toBe('login')
    expect(replace).toHaveBeenCalledWith({ query: { add: '1' } })
  })
})
