/**
 * [P0] 必测 — 登录页两态视图切换（login / register）
 * 目录：tests/login/p0/
 */
import { describe, expect, it, vi } from 'vitest'
import { useViewStateMachine } from '@/views/composables/useViewStateMachine'
import { mountComposable } from '../../helpers/mountComposable'

describe('[P0] useViewStateMachine', () => {
  it('初始态为 login', async () => {
    const clearError = vi.fn()
    const { result } = await mountComposable(() => useViewStateMachine(clearError))
    expect(result.viewState.value).toBe('login')
  })

  it('switchMode：清错并切换视图', async () => {
    const clearError = vi.fn()
    const { result } = await mountComposable(() => useViewStateMachine(clearError))
    result.switchMode('register')
    expect(clearError).toHaveBeenCalled()
    expect(result.viewState.value).toBe('register')
  })
})
