import axios from 'axios'

// ── Django API client (business modules) ──
const client = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
  timeout: 120000,  // 2min for LLM API responses
})

// ── AgentScope API client (AI service) ──
const agentscopeClient = axios.create({
  baseURL: '/agentscope',
  headers: { 'Content-Type': 'application/json' },
  timeout: 120000,
})

// ── JWT helpers — multi-account aware ──
// accounts pool: localStorage.auth_accounts (shared across tabs)
// active account: sessionStorage.auth_active  (per-tab, isolated)
const POOL_KEY = 'auth_accounts'
const ACTIVE_KEY = 'auth_active'

function readAuthStore() {
  let pool = {}
  // Migration: old single-token format → multi-account pool
  const oldToken = localStorage.getItem('access_token')
  if (oldToken) {
    const oldRefresh = localStorage.getItem('refresh_token')
    const oldUser = localStorage.getItem('username') || 'admin'
    pool = { [oldUser]: { access_token: oldToken, refresh_token: oldRefresh || '' } }
    localStorage.setItem(POOL_KEY, JSON.stringify(pool))
    sessionStorage.setItem(ACTIVE_KEY, oldUser)
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('username')
  } else {
    try {
      pool = JSON.parse(localStorage.getItem(POOL_KEY) || '{}')
    } catch { pool = {} }
  }
  const active = sessionStorage.getItem(ACTIVE_KEY) || Object.keys(pool)[0] || ''
  // Ensure active account exists in pool
  if (active && !pool[active]) {
    const first = Object.keys(pool)[0] || ''
    sessionStorage.setItem(ACTIVE_KEY, first)
    return { pool, active: first }
  }
  return { pool, active }
}

function writePool(pool) {
  localStorage.setItem(POOL_KEY, JSON.stringify(pool))
}

function getToken() {
  const { pool, active } = readAuthStore()
  return pool[active]?.access_token || ''
}

function setToken(token) {
  const { pool, active } = readAuthStore()
  if (active && pool[active]) {
    pool[active].access_token = token
    writePool(pool)
  }
}

function clearToken() {
  const { pool, active } = readAuthStore()
  if (active) {
    delete pool[active]
    writePool(pool)
    const remaining = Object.keys(pool)
    sessionStorage.setItem(ACTIVE_KEY, remaining.length > 0 ? remaining[0] : '')
  }
}

function getRefreshToken() {
  const { pool, active } = readAuthStore()
  return pool[active]?.refresh_token || ''
}

function getActiveUsername() {
  return sessionStorage.getItem(ACTIVE_KEY) || ''
}

// ── Request interceptor — inject JWT ──
function authInterceptor(config) {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
}

client.interceptors.request.use(authInterceptor)
agentscopeClient.interceptors.request.use(authInterceptor)

// ── Response interceptor — handle 401 + token refresh ──
async function authErrorInterceptor(err) {
  const originalRequest = err.config
  if (err.response?.status === 401 && !originalRequest._retry) {
    const refreshToken = getRefreshToken()
    if (refreshToken) {
      originalRequest._retry = true
      try {
        const resp = await axios.post('/api/ai/auth/refresh', {
          refresh_token: refreshToken,
        })
        if (resp.data.ok) {
          setToken(resp.data.access_token)
          originalRequest.headers.Authorization = `Bearer ${resp.data.access_token}`
          return axios(originalRequest)
        }
      } catch (e) {
        // refresh failed — remove account; redirect to login only if no accounts left
        clearToken()
        const { active } = readAuthStore()
        if (!active) {
          window.location.href = '/login'
        }
      }
    }
  }
  const msg = err.response?.data?.error || err.message
  // 404 通常是"资源不存在"的预期响应（如检查任务历史），不刷屏
  if (err.response?.status !== 404) {
    console.error('[API]', msg)
  }
  return Promise.reject(err)
}

client.interceptors.response.use(r => r, authErrorInterceptor)
agentscopeClient.interceptors.response.use(r => r, authErrorInterceptor)

/** 将 axios 错误转为用户可读的中文提示（避免暴露 status code 原文） */
function formatApiError(err, fallback = '操作失败，请稍后重试') {
  const data = err?.response?.data
  if (data && typeof data === 'object' && data.error) {
    return data.error
  }
  const body = typeof data === 'string' ? data : ''
  if (body.includes('uq_el_element') || body.includes('IntegrityError')) {
    return '该元素已在当前页面中（相同 resource-id 与位置），请到「元素管理」查看或更换目标页面'
  }
  const status = err?.response?.status
  if (status === 409) {
    return '该元素已在当前页面中，请到「元素管理」查看或更换目标页面'
  }
  if (status === 404) return '目标不存在，请刷新页面后重试'
  if (status === 401) return '登录已过期，请重新登录'
  if (status >= 500) return '服务暂时异常，请稍后重试'
  if (!err?.response) return '网络连接失败，请确认后端服务已启动'
  if (err.message?.includes('status code')) return fallback
  return err.message || fallback
}

export default client
export { agentscopeClient, getToken, setToken, clearToken, getRefreshToken, getActiveUsername, formatApiError }
