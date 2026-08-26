import { ElMessage } from 'element-plus'

/**
 * Unified API call wrapper with automatic error toast and loading state.
 *
 * Returns an `exec()` helper that wraps axios promises with:
 * - Automatic loading ref toggling
 * - Error toast via `ElMessage.error()` (suppressible with `silent: true`)
 * - Consistent return shape `{ status, ...data }`
 *
 * Rules (from .agents/skills/android-autotests-rules/references/frontend.md):
 * - 写操作: auto-toast on error (silent=false, default)
 * - 读操作: 可静默 (silent=true), 数据为空不报错
 *
 * @returns {{ exec: function }}
 *
 * @example
 *   const { exec } = useApi()
 *   const data = await exec(apiGetDevices(), { loading, silent: true })
 *   if (data?.status) devices.value = data.devices
 */
export function useApi() {
  /**
   * Execute an API call with automatic loading state and error handling.
   *
   * @param {Promise} promise — axios promise (returns `{ data }`)
   * @param {object} [opts]
   * @param {import('vue').Ref<boolean>} [opts.loading] — loading ref to toggle during the call
   * @param {boolean} [opts.silent=false] — if true, suppress error toast (for read ops)
   * @returns {Promise<{status: boolean, message?: string, ...}>} — the `data` from axios response, or `{status:false, message}` on failure
   */
  async function exec(promise, { loading, silent = false }: { loading?: any; silent?: boolean } = {}) {
    try {
      if (loading) loading.value = true
      const { data } = await promise
      if (!data?.status && !silent) {
        ElMessage.error(data?.message || '操作失败')
      }
      return data
    } catch (e) {
      if (!silent) {
        const msg =
          e?.response?.data?.message ||
          e?.message ||
          '网络异常，请检查服务状态'
        ElMessage.error(msg)
      }
      return { status: false, message: e }
    } finally {
      if (loading) loading.value = false
    }
  }

  return { exec }
}
