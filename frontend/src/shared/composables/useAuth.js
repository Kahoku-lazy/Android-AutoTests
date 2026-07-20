/** useAuth — Pinia store for multi-account token pool.
 *
 *  localStorage key:  auth_accounts
 *  Structure:  { active: "admin", accounts: { admin: { access_token, refresh_token }, ... } }
 *
 *  Usage:
 *    import { useAuthStore } from '@/shared/composables/useAuth.js'
 *    const auth = useAuthStore()
 *    auth.loginAccount('admin', access, refresh)
 *    auth.switchAccount('tester')
 */
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

const STORAGE_KEY = 'auth_accounts'

function _read() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}')
  } catch {
    return {}
  }
}

function _write(data) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
}

export const useAuthStore = defineStore('auth', () => {
  // ── State ──
  const raw = _read()
  const accounts = ref(raw.accounts || {})
  const activeUsername = ref(raw.active || '')

  // ── Getters ──
  const activeToken = computed(() => {
    if (!activeUsername.value) return ''
    return accounts.value[activeUsername.value]?.access_token || ''
  })

  const activeRefreshToken = computed(() => {
    if (!activeUsername.value) return ''
    return accounts.value[activeUsername.value]?.refresh_token || ''
  })

  const isLoggedIn = computed(() => !!activeUsername.value && !!activeToken.value)

  const accountList = computed(() =>
    Object.keys(accounts.value).map(username => ({
      username,
      isActive: username === activeUsername.value,
    })),
  )

  // ── Internal persist ──
  function _persist() {
    _write({
      active: activeUsername.value,
      accounts: { ...accounts.value },
    })
  }

  // ── Actions ──
  function loginAccount(username, access_token, refresh_token) {
    accounts.value = {
      ...accounts.value,
      [username]: { access_token, refresh_token },
    }
    activeUsername.value = username
    _persist()
  }

  function switchAccount(username) {
    if (accounts.value[username]) {
      activeUsername.value = username
      _persist()
    }
  }

  /** Logout: remove account(s). If current account, switch to first remaining.
   *  If no accounts remain, clear everything and return false (caller → redirect login). */
  function logoutAccount(username) {
    const target = username || activeUsername.value
    if (target) {
      const next = { ...accounts.value }
      delete next[target]
      accounts.value = next
    }

    if (target === activeUsername.value) {
      const remaining = Object.keys(accounts.value)
      if (remaining.length > 0) {
        activeUsername.value = remaining[0]
      } else {
        activeUsername.value = ''
        accounts.value = {}
        _persist()
        return false // no accounts left
      }
    }
    _persist()
    return true
  }

  /** Update token for the active account (called by api-client on refresh). */
  function updateActiveToken(access_token) {
    if (!activeUsername.value || !accounts.value[activeUsername.value]) return
    accounts.value = {
      ...accounts.value,
      [activeUsername.value]: {
        ...accounts.value[activeUsername.value],
        access_token,
      },
    }
    _persist()
  }

  return {
    accounts,
    activeUsername,
    activeToken,
    activeRefreshToken,
    isLoggedIn,
    accountList,
    loginAccount,
    switchAccount,
    logoutAccount,
    updateActiveToken,
  }
})
