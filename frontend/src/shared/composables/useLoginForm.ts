/** useLoginForm — 登录/注册表单校验（typed composable）。
 *
 *  纯函数式，无副作用。loginErrors 和 regErrors 各自独立计算。
 */
import { computed, type Ref, type ComputedRef } from 'vue'
import type { FieldErrors } from '@/shared/types/auth'

export interface UseLoginFormReturn {
  loginErrors: ComputedRef<FieldErrors>
  canLogin: ComputedRef<boolean>
  regErrors: ComputedRef<FieldErrors>
  canRegister: ComputedRef<boolean>
}

export function useLoginForm(
  loginUsername: Ref<string>,
  loginPassword: Ref<string>,
  regUsername: Ref<string>,
  regPassword: Ref<string>,
  regPassword2: Ref<string>,
  regEmail: Ref<string>,
): UseLoginFormReturn {
  const loginErrors = computed<FieldErrors>(() => {
    const errs: FieldErrors = {}
    if (!loginUsername.value) {
      errs.username = '请输入用户名'
    } else if (!loginUsername.value.trim()) {
      errs.username = '用户名不能为空白'
    } else if (loginUsername.value.length > 150) {
      errs.username = '用户名过长，最多150个字符'
    }
    if (!loginPassword.value) {
      errs.password = '请输入密码'
    }
    return errs
  })

  const canLogin = computed<boolean>(() => Object.keys(loginErrors.value).length === 0)

  const regErrors = computed<FieldErrors>(() => {
    // 与 RegisterSerializer.strip() 对齐后再校验
    const username = regUsername.value.trim()
    const email = regEmail.value.trim()
    const password = regPassword.value.trim()
    const password2 = regPassword2.value.trim()
    const errs: FieldErrors = {}
    if (!username) {
      errs.username = '请输入用户名'
    } else if (username.length < 3) {
      errs.username = '用户名至少 3 个字符'
    } else if (username.length > 20) {
      errs.username = '用户名最多 20 个字符'
    }
    if (!email) {
      errs.email = '请输入邮箱'
    } else if (!email.includes('@')) {
      errs.email = '邮箱格式不正确'
    }
    if (!password) {
      errs.password = '请输入密码'
    } else if (password.length < 6) {
      errs.password = '密码至少 6 位'
    }
    if (!password2) {
      errs.password2 = '请再次输入密码'
    } else if (password !== password2) {
      errs.password2 = '两次密码不一致'
    }
    return errs
  })

  const canRegister = computed<boolean>(() => Object.keys(regErrors.value).length === 0)

  return { loginErrors, canLogin, regErrors, canRegister }
}
