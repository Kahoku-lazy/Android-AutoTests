<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'
import WbLoader from './components/WbLoader.vue'
import AgentRouteCard from './components/AgentRouteCard.vue'
import KnowledgeBase from './KnowledgeBase.vue'
import EvaluatorTab from './EvaluatorTab.vue'
import ToolboxPanel from './components/ToolboxPanel.vue'
import TaskBoard from './components/TaskBoard.vue'
import { useAgentBoard } from './index.logic'
import { useAuthUser } from '@/shared/composables/useAuthUser'
import type { ViewMode } from '@/shared/types/ai'

const router = useRouter()
const route = useRoute()
const dutyRosterRef = ref<HTMLElement | null>(null)
const {
  agents, loading, agentsError,
  PAGE_HEADER, testingRoute, routeTestResults,
  loadAgents, editAgent, testConnection,
} = useAgentBoard(dutyRosterRef)

const { isSuperuser } = useAuthUser()
const isAdmin = computed(() => isSuperuser.value === true)

// 两条助手线路（每条线路独立 name/avatar，存于 route_configs）
const routeCards = computed(() => {
  const agent = agents.value[0]
  const configs = agent?.route_configs || {}
  const fallbackName = agent?.name || '未命名助手'
  const fallbackAvatar = agent?.avatar || agent?.avatar_url || '🤖'
  return [
    {
      key: 'device_control',
      label: '控制设备',
      icon: '📱',
      config: configs.device_control,
      agentName: configs.device_control?.name || fallbackName,
      agentAvatar: configs.device_control?.avatar || fallbackAvatar,
    },
    {
      key: 'platform_task',
      label: '平台任务',
      icon: '🧭',
      config: configs.platform_task,
      agentName: configs.platform_task?.name || fallbackName,
      agentAvatar: configs.platform_task?.avatar || fallbackAvatar,
    },
  ]
})

// ── 视图（侧边栏子项路由驱动，/ai-assistant/agents|toolbox|knowledge|evaluator）──
const VIEW_BY_PATH: Record<string, ViewMode> = {
  '/ai-assistant/agents': 'agents',
  '/ai-assistant/toolbox': 'toolbox',
  '/ai-assistant/knowledge': 'knowledge',
  '/ai-assistant/evaluator': 'evaluator',
}
const viewMode = computed<ViewMode>(() => VIEW_BY_PATH[route.path] || 'agents')

// ── 顶部 WorkbenchHeader 随侧边栏子项变化 ──
const VIEW_META: Record<ViewMode, { title: string; subtitle: string }> = {
  agents: {
    title: '平台小助手 Platform Assistant',
    subtitle: '助手看板 + 任务卡片列表：配置两条线路、新建任务并下发执行',
  },
  toolbox: {
    title: 'AI工具箱 AI Toolbox',
    subtitle: '集中管理跨智能体复用的 Skill、MCP 与扩展',
  },
  knowledge: {
    title: '知识库 Knowledge Base',
    subtitle: 'ChromaDB 向量库状态与可索引文档，支持重建索引',
  },
  evaluator: {
    title: '评测中心 Evaluation Center',
    subtitle: '自然语言用例生成与执行：描述输入 → 设备选择 → 生成或直接执行',
  },
}
const pageMeta = computed(() => VIEW_META[viewMode.value])
</script>

<template>
  <div class="doc-page wb-shell ai-workbench">
    <WorkbenchHeader
      :title="pageMeta.title"
      :subtitle="pageMeta.subtitle"
      :icon="PAGE_HEADER.icon"
      :icon-gradient="PAGE_HEADER.iconGradient"
    />


    <div class="doc-body">
      <template v-if="viewMode === 'agents'">
      <section class="doc-section duty-section">
        <div class="doc-section__header">
          <h3 class="doc-section__title">平台小助手<span class="doc-tag">Assistant</span></h3>
          <span class="filter-count">{{ routeCards.length }} 个助手</span>
        </div>
        <ErrorState v-if="agentsError" :message="agentsError" @retry="loadAgents" />
        <div v-else class="route-card-grid" v-loading="loading">
          <div v-if="loading && !agents.length" class="ai-loading-wrap">
            <WbLoader /><span>正在加载智能体…</span>
          </div>
          <AgentRouteCard
            v-for="rc in routeCards" :key="rc.key"
            :label="rc.label" :icon="rc.icon" :config="rc.config"
            :agent-name="rc.agentName"
            :agent-avatar="rc.agentAvatar"
            :can-manage="isAdmin"
            :testing="testingRoute === rc.key"
            :test-results="routeTestResults[rc.key]"
            @edit="editAgent(agents[0]?.id ?? 0, rc.key)"
            @test="agents[0] && testConnection(agents[0], rc.key)"
          />
          <EmptyState v-if="!agents.length && !loading" icon="🤖" text="还没有智能体" :hint="'请联系管理员配置智能体'" />
        </div>
      </section>

      <!-- 模块 2：任务卡片列表（新建任务弹窗 + 卡片式列表） -->
      <TaskBoard />
      </template>

      <ToolboxPanel v-if="viewMode === 'toolbox'" class="tb-host" :can-manage="isAdmin" />
      <KnowledgeBase v-if="viewMode === 'knowledge'" class="kb-host" :can-manage="isAdmin" />
      <EvaluatorTab v-if="viewMode === 'evaluator'" class="eval-host" />
    </div>
  </div>
</template>

<style src="./index.style.css" scoped></style>

<style scoped>
.route-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  align-items: start;
}
</style>
