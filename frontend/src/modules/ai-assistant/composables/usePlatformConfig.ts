/** usePlatformConfig — 平台唯一智能体的能力开关 + 工作区 Skills 编排。
 *
 * 数据源：GET /api/ai/platform-config（enable_* 开关 + skills_config）、
 *         GET /api/ai/available-skills（workspace 技能清单）。
 * 写：POST /api/ai/platform-config/update（仅超级管理员）。
 * 知识库开关与文档范围由知识库页（KnowledgeBase.vue）管理，此处只读不写。
 */
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  fetchPlatformConfig,
  updatePlatformConfig,
  fetchAvailableSkills,
} from '../api/toolbox'

interface WorkspaceSkill {
  name: string
  description?: string
}

const CAPABILITY_LABELS: Record<string, string> = {
  enable_business_tools: '业务工具',
  enable_workspace_tools: '内置工具',
  enable_mcp_tools: 'MCP 工具',
  enable_skills: '自定义 Skills',
}

export function usePlatformConfig() {
  const config = ref<Record<string, any>>({
    enable_workspace_tools: false,
    enable_business_tools: false,
    enable_mcp_tools: false,
    enable_skills: false,
    enable_knowledge_base: false,
    skills_config: {},
    knowledge_sources: {},
  })
  const workspaceSkills = ref<WorkspaceSkill[]>([])
  const loading = ref(false)

  async function load() {
    loading.value = true
    try {
      const [cfgData, skillsData] = await Promise.all([
        fetchPlatformConfig(),
        fetchAvailableSkills(),
      ])
      if (cfgData.status && cfgData.data) config.value = { ...config.value, ...cfgData.data }
      if (skillsData.status) workspaceSkills.value = (skillsData.data?.skills || []) as WorkspaceSkill[]
    } catch (e) {
      console.error('Failed to load platform config:', e)
    }
    loading.value = false
  }

  function toggleFlag(key: string, value: boolean) {
    const prev = config.value[key]
    config.value[key] = value  // 乐观更新
    updatePlatformConfig({ [key]: value } as any).then((data) => {
      if (!data.status) {
        config.value[key] = prev
        ElMessage.error(data.message || '操作失败')
      }
    }).catch(() => {
      config.value[key] = prev
      ElMessage.error('操作失败')
    })
  }

  function isSkillEnabled(name: string) {
    const cfg = (config.value.skills_config || {}) as Record<string, boolean>
    return cfg[name] !== false
  }

  function toggleSkill(name: string) {
    const cfg = { ...((config.value.skills_config || {}) as Record<string, boolean>) }
    cfg[name] = !isSkillEnabled(name)
    config.value.skills_config = cfg  // 乐观更新
    updatePlatformConfig({ skills_config: cfg }).then((data) => {
      if (!data.status) ElMessage.error(data.message || '操作失败')
    }).catch(() => ElMessage.error('操作失败'))
  }

  function skillEnabledCount() {
    return workspaceSkills.value.filter((s) => isSkillEnabled(s.name)).length
  }

  onMounted(load)

  return {
    config, workspaceSkills, loading, load,
    CAPABILITY_LABELS, toggleFlag, isSkillEnabled, toggleSkill, skillEnabledCount,
  }
}
