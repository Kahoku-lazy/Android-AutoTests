/** usePlatformConfig — 平台唯一智能体的能力开关编排。
 *
 * 数据源：GET /api/ai/platform-config（enable_* 开关）。
 * 写：POST /api/ai/platform-config/update（仅超级管理员）。
 * 知识库开关与文档范围由知识库页（KnowledgeBase.vue）管理，此处只读不写。
 */
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchPlatformConfig, updatePlatformConfig } from '../api/toolbox'

export function usePlatformConfig() {
  const config = ref<Record<string, unknown>>({
    enable_workspace_tools: false,
    enable_business_tools: false,
    enable_mcp_tools: false,
    enable_skills: false,
    enable_knowledge_base: false,
    skills_config: {},
    knowledge_sources: {},
  })
  const loading = ref(false)

  async function load() {
    loading.value = true
    try {
      const cfgData = await fetchPlatformConfig()
      if (cfgData.status && cfgData.data) config.value = { ...config.value, ...cfgData.data }
    } catch (e) {
      console.error('Failed to load platform config:', e)
    }
    loading.value = false
  }

  function toggleFlag(key: string, value: boolean) {
    const prev = config.value[key]
    config.value[key] = value
    updatePlatformConfig({ [key]: value }).then((data) => {
      if (!data.status) {
        config.value[key] = prev
        ElMessage.error(data.message || '操作失败')
      }
    }).catch(() => {
      config.value[key] = prev
      ElMessage.error('操作失败')
    })
  }

  onMounted(load)

  return {
    config, loading, load, toggleFlag,
  }
}
