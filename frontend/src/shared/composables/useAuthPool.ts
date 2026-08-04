/** useAuthPool — 多账号 token 池管理（typed composable）。
 *
 *  存储格式（与 shared/api-client.js 兼容）：
 *    localStorage.auth_accounts  = {admin: {access_token, refresh_token}, tester: {...}}
 *    sessionStorage.auth_active  = "admin"  (per-tab 隔离)
 */
import { ref, computed, onMounted, onUnmounted, type Ref, type ComputedRef } from 'vue'
import type { AuthPool } from '@/shared/types/auth'

const POOL_KEY = 'auth_accounts'
const ACTIVE_KEY = 'auth_active'

// ── 纯函数：读写底层 storage ──

function readPool(): AuthPool {
  try { return JSON.parse(localStorage.getItem(POOL_KEY) || '{}') }
  catch { return {} }
}

function writePool(pool: AuthPool): void {
  localStorage.setItem(POOL_KEY, JSON.stringify(pool))
}

function getActive(): string {
  return sessionStorage.getItem(ACTIVE_KEY) || Object.keys(readPool())[0] || ''
}

function setActive(username: string): void {
  sessionStorage.setItem(ACTIVE_KEY, username)
}

// ── 导出接口 ──

export interface UseAuthPoolReturn {
  activeAccount: Ref<string>
  accountList: ComputedRef<string[]>
  loginAccount: (username: string, access_token: string, refresh_token: string) => void
  switchAccount: (username: string) => boolean
  logoutAccount: () => boolean
}

// ── Composable ──

export function useAuthPool(): UseAuthPoolReturn {
  const pool = ref<AuthPool>(readPool())
  const activeAccount = ref<string>(getActive())

  const accountList = computed<string[]>(() => Object.keys(pool.value))

  function _refresh(): void {
    pool.value = readPool()
    activeAccount.value = getActive()
  }

  // 跨 tab 同步：其他 tab 修改 auth_accounts 时自动刷新
  function _onStorage(e: StorageEvent): void {
    if (e.key === POOL_KEY) _refresh()
  }

  onMounted(() => window.addEventListener('storage', _onStorage))
  onUnmounted(() => window.removeEventListener('storage', _onStorage))

  /** 添加/更新账号到池中，并设为当前 tab 的 active */
  function loginAccount(username: string, access_token: string, refresh_token: string): void {
    const next: AuthPool = { ...pool.value, [username]: { access_token, refresh_token } }
    writePool(next)
    setActive(username)
    pool.value = next
    activeAccount.value = username
  }

  /** 切换到已有账号（调用后需要 reload 以刷新 token） */
  function switchAccount(username: string): boolean {
    if (!pool.value[username]) return false
    setActive(username)
    return true
  }

  /** 登出当前 active 账号。有剩余账号则切换，无则返回 false（调用方跳转 /login） */
  function logoutAccount(): boolean {
    const target = activeAccount.value
    if (!target) return false
    const next: AuthPool = { ...pool.value }
    delete next[target]
    writePool(next)
    pool.value = next

    const remaining = Object.keys(next)
    if (remaining.length > 0) {
      setActive(remaining[0])
      activeAccount.value = remaining[0]
      return true
    }
    setActive('')
    activeAccount.value = ''
    return false
  }

  return {
    activeAccount,
    accountList,
    loginAccount,
    switchAccount,
    logoutAccount,
  }
}
