/** useAuthPool — 多账号 token 池管理（typed composable）。
 *
 *  存储委托给 token-storage.ts（唯一真相源）。
 *  与 api-client.ts 共享同一份存储逻辑，消除双源竞态。
 */
import { ref, computed, onMounted, onUnmounted, type Ref, type ComputedRef } from 'vue'
import type { AuthPool } from "@/shared/types/auth"
import {
  readPool,
  writePool,
  getActive,
  setActive,
  POOL_KEY,
} from "@/shared/auth/token-storage"

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
