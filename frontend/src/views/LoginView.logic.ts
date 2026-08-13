/** LoginView 逻辑层 — 薄编排器，组合子 composable。
 *
 *  作为 composable 导出，LoginView.vue 的 <script setup> 调用 useLoginView()
 *  并解构所有返回值供模板绑定。
 */
import { ref, type Ref, type ComputedRef } from "vue"
import { ElMessage } from "element-plus"

import { useAuthPool } from "@/shared/composables/useAuthPool"
import { useLoginForm } from "@/shared/composables/useLoginForm"
import type { ViewState, FieldErrors } from "@/shared/types/auth"

import { useViewStateMachine } from "./composables/useViewStateMachine"
import { useSavedUsername } from "./composables/useSavedUsername"
import { useAuthFlow } from "./composables/useAuthFlow"
import { useHeroImage } from "./composables/useHeroImage"

export interface LoginViewState {
  activeAccount: Ref<string>
  accountList: ComputedRef<string[]>
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
  heroImageSrc: string
  heroImageVisible: Ref<boolean>
  serverError: Ref<string>
  clearServerError: () => void
  handleLogin: () => Promise<void>
  handleRegister: () => Promise<void>
  switchMode: (m: ViewState) => void
  onSwitchToExisting: () => void
  onAddNewAccount: () => void
  onHeroImageError: () => void
}

export function useLoginView(): LoginViewState {
  // ── 子 composable 组合 ──

  const auth = useAuthPool()
  const { loginUsername, rememberMe, saveUsername } = useSavedUsername()
  const { heroImageSrc, heroImageVisible, onHeroImageError } = useHeroImage()

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
  const { loading, serverError, clearServerError, authenticate } = useAuthFlow({
    auth,
    saveUsername,
  })

  const { viewState, switchMode: baseSwitchMode, onSwitchToExisting, onAddNewAccount } =
    useViewStateMachine(auth.accountList, clearServerError)

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
    activeAccount: auth.activeAccount,
    accountList: auth.accountList,
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
    heroImageSrc,
    heroImageVisible,
    serverError,
    clearServerError,
    handleLogin,
    handleRegister,
    switchMode,
    onSwitchToExisting,
    onAddNewAccount,
    onHeroImageError,
  }
}
