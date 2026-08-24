<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'
import WbLoader from './components/WbLoader.vue'
import AgentStickyNote from './components/AgentStickyNote.vue'
import KnowledgeBase from './KnowledgeBase.vue'
import EvaluatorTab from './EvaluatorTab.vue'
import ToolboxPanel from './components/ToolboxPanel.vue'
import { useAgentBoard } from './index.logic'
import { agentDetailRoute } from './constants'
import type { ViewMode } from '@/shared/types/ai'

const router = useRouter()
const route = useRoute()
const dutyRosterRef = ref<HTMLElement | null>(null)
const {
  agents, loading, agentsError, testingId, confirmingId, pendingModels,
  PAGE_HEADER, noteRotation, tapeHue,
  agentStatusClass, agentStatusText, getModelOptions,
  loadAgents, confirmModel, deleteAgent, testConnection,
  openAgent, editAgent, onAgentCardClick,
} = useAgentBoard(dutyRosterRef)

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
    title: '智能体看板 Agent Board',
    subtitle: '管理智能体：创建、编辑、连接测试与模型切换',
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
    >
      <template #actions>
        <el-button class="wb-btn wb-btn--sky" type="primary" @click="router.push(agentDetailRoute('new'))">+ 新建智能体</el-button>
      </template>
    </WorkbenchHeader>

    <div class="doc-body">
      <template v-if="viewMode === 'agents'">
      <section class="doc-section duty-section">
        <div class="doc-section__header">
          <h3 class="doc-section__title">智能体看板<span class="doc-tag">Agents</span></h3>
          <span class="filter-count">{{ agents.length }} 张便签</span>
        </div>
        <ErrorState v-if="agentsError" :message="agentsError" @retry="loadAgents" />
        <div v-else ref="dutyRosterRef" class="dot-board duty-roster" v-loading="loading">
          <div v-if="loading && !agents.length" class="ai-loading-wrap">
            <WbLoader /><span>正在加载智能体…</span>
          </div>
          <AgentStickyNote
            v-for="a in agents" :key="a.id" :agent="a"
            :rotation="noteRotation(a)" :tape-hue="tapeHue(a)"
            :pending-model="pendingModels[a.id]" :confirming="confirmingId === a.id"
            :testing="testingId === a.id" :status-class="agentStatusClass(a)"
            :status-text="agentStatusText(a)" :model-options="getModelOptions(a, pendingModels[a.id])"
            @update:pending-model="pendingModels[a.id] = $event"
            @confirm-model="confirmModel(a)" @chat="openAgent(a)"
            @edit="editAgent(a.id)" @test="testConnection(a)"
            @delete="deleteAgent(a)" @select="onAgentCardClick"
          />
          <EmptyState v-if="!agents.length && !loading" icon="🤖" text="还没有智能体" hint="点击「+ 新建智能体」贴上第一张便签" />
        </div>
      </section>

      </template>

      <ToolboxPanel v-if="viewMode === 'toolbox'" class="tb-host" />
      <KnowledgeBase v-if="viewMode === 'knowledge'" class="kb-host" />
      <EvaluatorTab v-if="viewMode === 'evaluator'" class="eval-host" />
    </div>
  </div>
</template>

<style src="./index.style.css" scoped></style>
