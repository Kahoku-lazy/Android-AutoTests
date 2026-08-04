/** LoginView 逻辑层 — 状态、事件、计算（大脑）。
 *
 *  作为 composable 导出，LoginView.vue 的 <script setup> 调用 useLoginView()
 *  并解构所有返回值供模板绑定。
 */
import { ref, computed, onMounted, type Ref, type ComputedRef } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'

import { login, register } from '@/shared/api/auth'
import { useAuthPool, type UseAuthPoolReturn } from '@/shared/composables/useAuthPool'
import { useLoginForm, type UseLoginFormReturn } from '@/shared/composables/useLoginForm'
import type { ViewState, FieldErrors } from '@/shared/types/auth'

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
  loading: Ref<boolean>
  loginErrors: ComputedRef<FieldErrors>
  canLogin: ComputedRef<boolean>
  regErrors: ComputedRef<FieldErrors>
  canRegister: ComputedRef<boolean>
  heroImageSrc: string
  heroImageVisible: Ref<boolean>
  handleLogin: () => Promise<void>
  handleRegister: () => Promise<void>
  switchMode: (m: string) => void
  onSwitchToExisting: () => void
  onAddNewAccount: () => void
}

export function useLoginView(): LoginViewState {
  const router = useRouter()
  const route = useRoute()

  // ── Auth pool ──
  const { activeAccount, accountList, loginAccount } = useAuthPool()

  // ── View state machine ──
  const viewState = ref<ViewState>('login')

  onMounted(() => {
    if (accountList.value.length > 0 && !route.query.add) {
      viewState.value = 'switchPrompt'
    }
  })

  function onSwitchToExisting() {
    router.push('/dashboard')
  }

  function onAddNewAccount() {
    viewState.value = 'login'
    router.replace({ query: { add: '1' } })
  }

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
  const mode = computed(() => viewState.value === 'register' ? 'register' : 'login') as Ref<'login' | 'register'>

  // ── 校验 ──
  const { loginErrors, canLogin, regErrors, canRegister } =
    useLoginForm(mode, loginUsername, loginPassword, regUsername, regPassword, regPassword2)

  // ── 操作 ──
  async function handleLogin() {
    if (!canLogin.value) {
      ElMessage.warning(Object.values(loginErrors.value)[0])
      return
    }
    loading.value = true
    try {
      const data = await login(loginUsername.value, loginPassword.value)
      if (data.ok) {
        loginAccount(loginUsername.value, data.access_token, data.refresh_token)
        if (rememberMe.value) {
          localStorage.setItem('saved_username', loginUsername.value)
        } else {
          localStorage.removeItem('saved_username')
        }
        ElMessage.success('登录成功，正在跳转...')
        router.push('/dashboard')
      } else {
        ElMessage.error(data.error || '登录失败')
      }
    } catch (e: any) {
      ElMessage.error(e.response?.data?.error || '服务异常，请检查后端是否启动')
    } finally {
      loading.value = false
    }
  }

  async function handleRegister() {
    if (!canRegister.value) {
      ElMessage.warning(Object.values(regErrors.value)[0])
      return
    }
    loading.value = true
    try {
      const data = await register(regUsername.value.trim(), regPassword.value)
      if (data.ok) {
        loginAccount(regUsername.value.trim(), data.access_token, data.refresh_token)
        ElMessage.success('注册成功，正在进入平台...')
        setTimeout(() => router.push('/dashboard'), 600)
      } else {
        ElMessage.error(data.error || '注册失败')
      }
    } catch (e: any) {
      ElMessage.error(e.response?.data?.error || '服务异常，请检查后端是否启动')
    } finally {
      loading.value = false
    }
  }

  function switchMode(m: string) {
    viewState.value = m as ViewState
  }

  // ── 视觉图 ──
  const heroImageSrc = '/login/login-hero.jpg'
  const heroImageVisible = ref(true)

  return {
    activeAccount,
    accountList,
    viewState,
    loginUsername,
    loginPassword,
    rememberMe,
    regUsername,
    regPassword,
    regPassword2,
    loading,
    loginErrors,
    canLogin,
    regErrors,
    canRegister,
    heroImageSrc,
    heroImageVisible,
    handleLogin,
    handleRegister,
    switchMode,
    onSwitchToExisting,
    onAddNewAccount,
  }
}
