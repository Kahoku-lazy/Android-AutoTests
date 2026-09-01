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
  PAGE_HEADER, testingId,
  loadAgents, editAgent, testConnection,
} = useAgentBoard(dutyRosterRef)

const { isSuperuser } = useAuthUser()
const isAdmin = computed(() => isSuperuser.value === true)

// 两条助手线路（从平台唯一智能体的 route_configs 读取）
const routeCards = computed(() => [
  { key: 'device_control', label: '控制设备', icon: '📱', config: agents.value[0]?.route_configs?.device_control },
  { key: 'platform_task', label: '平台任务', icon: '🧭', config: agents.value[0]?.route_configs?.platform_task },
])

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
            :can-manage="isAdmin"
            :testing="testingId === agents[0]?.id"
            @edit="editAgent(agents[0]?.id ?? 0, rc.key)"
            @test="agents[0] && testConnection(agents[0])"
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
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  align-items: start;
}
</style>
