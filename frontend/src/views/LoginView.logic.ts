/**
 * 登录页逻辑：在登录与注册之间切换，收集表单并提交认证。
 *
 * 业务：
 * - 登录：账号、密码、记住账号
 * - 注册：账号、邮箱、密码、确认密码
 * - 校验字段并决定能否提交；不通过时提示，通过后提交
 * - 展示服务端错误，关闭后清除
 * - 切换登录/注册时，清掉将进入的一侧表单和当前错误提示
 */
import { ref, type Ref, type ComputedRef } from "vue"
import { ElMessage } from "element-plus"

import { useLoginForm } from "@/shared/composables/useLoginForm"
import type { ViewState, FieldErrors } from "@/shared/types/auth"

import { useViewStateMachine } from "./composables/useViewStateMachine"
import { useSavedUsername } from "./composables/useSavedUsername"
import { useAuthFlow } from "./composables/useAuthFlow"

export interface LoginViewState {
  viewState: Ref<ViewState>
  loginUsername: Ref<string>
  loginPassword: Ref<string>
  rememberMe: Ref<boolean>
  regUsername: Ref<string>
  regPassword: Ref<string>
  regPassword2: Ref<string>
  regEmail: Ref<string>
  loading: Ref<boolean>
  loginErrors: ComputedRef<FieldErrors>
  canLogin: ComputedRef<boolean>
  regErrors: ComputedRef<FieldErrors>
  canRegister: ComputedRef<boolean>
  serverError: Ref<string>
  clearServerError: () => void
  handleLogin: () => Promise<void>
  handleRegister: () => Promise<void>
  switchMode: (m: ViewState) => void
}

export function useLoginView(): LoginViewState {
  // ── 子 composable 组合 ──

  const { loginUsername, rememberMe, saveUsername } = useSavedUsername()

  // ── 表单 ref ──
  const loginPassword = ref("")
  const regUsername = ref("")
  const regPassword = ref("")
  const regPassword2 = ref("")
  const regEmail = ref("")

  // ── 校验 ──
  const { loginErrors, canLogin, regErrors, canRegister } = useLoginForm(
    loginUsername,
    loginPassword,
    regUsername,
    regPassword,
    regPassword2,
    regEmail,
  )

  // ── 认证流程（必须在 useViewStateMachine 之前，因为后者需要 clearServerError）──
  const { loading, serverError, clearServerError, authenticate } = useAuthFlow({ saveUsername })

  const { viewState, switchMode: baseSwitchMode } = useViewStateMachine(clearServerError)

  /** 切换登录/注册时清空目标表单 */
  function switchMode(m: ViewState) {
    if (m === "register") {
      regUsername.value = ""
      regPassword.value = ""
      regPassword2.value = ""
      regEmail.value = ""
    }
    if (m === "login") {
      loginPassword.value = ""
    }
    baseSwitchMode(m)
  }

  // ── 便捷包装：保持原 LoginView.vue 的 @submit 绑定方式 ──
  async function handleLogin() {
    if (!canLogin.value) {
      const firstError = loginErrors.value.username || loginErrors.value.password
      ElMessage.warning(firstError || "请完善表单")
      return
    }
    await authenticate({
      mode: "login",
      username: loginUsername.value,
      password: loginPassword.value,
    })
  }

  async function handleRegister() {
    if (!canRegister.value) {
      const firstError =
        regErrors.value.username ||
        regErrors.value.email ||
        regErrors.value.password ||
        regErrors.value.password2
      ElMessage.warning(firstError || "请完善表单")
      return
    }
    await authenticate({
      mode: "register",
      username: regUsername.value,
      password: regPassword.value,
      password2: regPassword2.value,
      email: regEmail.value,
    })
  }

  return {
    viewState,
    loginUsername,
    loginPassword,
    rememberMe,
    regUsername,
    regPassword,
    regPassword2,
    regEmail,
    loading,
    loginErrors,
    canLogin,
    regErrors,
    canRegister,
    serverError,
    clearServerError,
    handleLogin,
    handleRegister,
    switchMode,
  }
}
