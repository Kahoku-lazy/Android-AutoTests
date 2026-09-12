/** usePlatformTools — AI 工具箱「平台业务工具」目录 + 全局启停编排。
 *
 * 数据源 GET /api/ai/available-tools（含每个工具的全局 enabled 状态）；
 * 启停写 POST /api/ai/platform-tools/toggle（仅超级管理员）。
 * 智能体配置页不再逐工具勾选，只保留「业务工具」总开关——选用哪个由 AI 工具箱全局决定。
 */
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  fetchPlatformTools,
  togglePlatformTool,
  type PlatformToolCategory,
} from '../api/toolbox'

export function usePlatformTools() {
  const categories = ref<PlatformToolCategory[]>([])
  const loading = ref(false)
  const toggling = ref(false)
  // 装配台：默认折叠，避免首屏被业务工具挤满
  const expanded = ref<string[]>([])

  async function loadPlatformTools() {
    loading.value = true
    try {
      const data = await fetchPlatformTools()
      if (data.status) {
        categories.value = data.data?.categories || []
        // 仅保留用户已展开的模块；初次加载保持折叠
        const keys = new Set(categories.value.map((c) => c.key))
        expanded.value = expanded.value.filter((k) => keys.has(k))
      }
    } catch (e) {
      console.error('Failed to load platform tools:', e)
    }
    loading.value = false
  }

  function applyEnabled(name: string, enabled: boolean) {
    for (const cat of categories.value) {
      const tool = cat.tools.find((t) => t.name === name)
      if (tool) tool.enabled = enabled
    }
  }

  function enabledCount(cat: PlatformToolCategory) {
    return cat.tools.filter((t) => t.enabled).length
  }

  function allEnabled(cat: PlatformToolCategory) {
    return cat.tools.length > 0 && cat.tools.every((t) => t.enabled)
  }

  async function toggleTool(name: string, enabled: boolean) {
    if (toggling.value) return
    toggling.value = true
    applyEnabled(name, enabled)  // 乐观更新
    try {
      const data = await togglePlatformTool({ name, enabled })
      if (!data.status) {
        applyEnabled(name, !enabled)
        ElMessage.error(data.message || '操作失败')
      }
    } catch (e) {
      applyEnabled(name, !enabled)
      ElMessage.error('操作失败')
    } finally {
      toggling.value = false
    }
  }

  async function toggleCategory(cat: PlatformToolCategory, enabled: boolean) {
    if (toggling.value) return
    const names = cat.tools.map((t) => t.name)
    toggling.value = true
    names.forEach((n) => applyEnabled(n, enabled))  // 乐观更新
    try {
      const data = await togglePlatformTool({ category: cat.key, enabled })
      if (!data.status) {
        names.forEach((n) => applyEnabled(n, !enabled))
        ElMessage.error(data.message || '操作失败')
      }
    } catch (e) {
      names.forEach((n) => applyEnabled(n, !enabled))
      ElMessage.error('操作失败')
    } finally {
      toggling.value = false
    }
  }

  onMounted(() => loadPlatformTools())

  return {
    categories, loading, toggling, expanded, loadPlatformTools,
    enabledCount, allEnabled, toggleTool, toggleCategory,
  }
}
