/**
 * [P0] 必测 — 登录/注册表单校验（纯逻辑，无副作用）
 * 目录：tests/login/p0/
 */
import { ref } from 'vue'
import { describe, expect, it } from 'vitest'
import { useLoginForm } from '@/shared/composables/useLoginForm'

function makeForm(overrides: Partial<{
  loginUsername: string
  loginPassword: string
  regUsername: string
  regPassword: string
  regPassword2: string
  regEmail: string
}> = {}) {
  return useLoginForm(
    ref(overrides.loginUsername ?? ''),
    ref(overrides.loginPassword ?? ''),
    ref(overrides.regUsername ?? ''),
    ref(overrides.regPassword ?? ''),
    ref(overrides.regPassword2 ?? ''),
    ref(overrides.regEmail ?? ''),
  )
}

describe('[P0] useLoginForm', () => {
  it('登录字段为空时不能提交', () => {
    const { loginErrors, canLogin } = makeForm()
    expect(canLogin.value).toBe(false)
    expect(loginErrors.value.username).toBe('请输入用户名')
    expect(loginErrors.value.password).toBe('请输入密码')
  })

  it('登录用户名仅空白时提示错误', () => {
    const { loginErrors, canLogin } = makeForm({
      loginUsername: '   ',
      loginPassword: 'x',
    })
    expect(canLogin.value).toBe(false)
    expect(loginErrors.value.username).toBe('用户名不能为空白')
  })

  it('合法登录字段可通过', () => {
    const { loginErrors, canLogin } = makeForm({
      loginUsername: 'alice',
      loginPassword: 'secret',
    })
    expect(canLogin.value).toBe(true)
    expect(loginErrors.value).toEqual({})
  })

  it('注册用户名过短', () => {
    const { regErrors, canRegister } = makeForm({
      regUsername: 'ab',
      regEmail: 'a@b.com',
      regPassword: '123456',
      regPassword2: '123456',
    })
    expect(canRegister.value).toBe(false)
    expect(regErrors.value.username).toBe('用户名至少 3 个字符')
  })

  it('注册邮箱无 @', () => {
    const { regErrors } = makeForm({
      regUsername: 'alice',
      regEmail: 'bad',
      regPassword: '123456',
      regPassword2: '123456',
    })
    expect(regErrors.value.email).toBe('邮箱格式不正确')
  })

  it('注册密码过短', () => {
    const { regErrors } = makeForm({
      regUsername: 'alice',
      regEmail: 'a@b.com',
      regPassword: '123',
      regPassword2: '123',
    })
    expect(regErrors.value.password).toBe('密码至少 6 位')
  })

  it('注册两次密码不一致', () => {
    const { regErrors, canRegister } = makeForm({
      regUsername: 'bob',
      regEmail: 'bob@example.com',
      regPassword: '123456',
      regPassword2: '654321',
    })
    expect(canRegister.value).toBe(false)
    expect(regErrors.value.password2).toBe('两次密码不一致')
  })

  it('注册密码 trim 后过短', () => {
    const { regErrors, canRegister } = makeForm({
      regUsername: 'alice',
      regEmail: 'a@b.com',
      regPassword: '  123  ',
      regPassword2: '  123  ',
    })
    expect(canRegister.value).toBe(false)
    expect(regErrors.value.password).toBe('密码至少 6 位')
  })

  it('注册字段含首尾空格但 trim 后合法可通过', () => {
    const { regErrors, canRegister } = makeForm({
      regUsername: '  bob  ',
      regEmail: '  bob@example.com  ',
      regPassword: '  123456  ',
      regPassword2: '  123456  ',
    })
    expect(canRegister.value).toBe(true)
    expect(regErrors.value).toEqual({})
  })

  it('合法注册字段可通过', () => {
    const { regErrors, canRegister } = makeForm({
      regUsername: 'bob',
      regEmail: 'bob@example.com',
      regPassword: '123456',
      regPassword2: '123456',
    })
    expect(canRegister.value).toBe(true)
    expect(regErrors.value).toEqual({})
  })
})
