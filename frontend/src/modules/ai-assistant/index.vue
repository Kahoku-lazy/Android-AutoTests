<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
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

const router = useRouter()
const dutyRosterRef = ref<HTMLElement | null>(null)
const {
  viewMode, agents, loading, agentsError, testingId, confirmingId, pendingModels,
  PAGE_HEADER, noteRotation, tapeHue,
  agentStatusClass, agentStatusText, getModelOptions,
  loadAgents, confirmModel, deleteAgent, testConnection,
  openAgent, editAgent, onAgentCardClick,
} = useAgentBoard(dutyRosterRef)
</script>

<template>
  <div class="doc-page wb-shell ai-workbench">
    <WorkbenchHeader
      :title="PAGE_HEADER.title"
      :subtitle="PAGE_HEADER.subtitle"
      :icon="PAGE_HEADER.icon"
      :icon-gradient="PAGE_HEADER.iconGradient"
    >
      <template #actions>
        <el-button class="wb-btn wb-btn--sky" type="primary" @click="router.push(agentDetailRoute('new'))">+ 新建智能体</el-button>
      </template>
    </WorkbenchHeader>

    <div class="doc-body">
      <div class="view-tabs">
        <button :class="['view-tab', { active: viewMode === 'agents' }]" @click="viewMode = 'agents'">🤖 智能体看板</button>
        <button :class="['view-tab', { active: viewMode === 'toolbox' }]" @click="viewMode = 'toolbox'">🧰 AI工具箱</button>
        <button :class="['view-tab', { active: viewMode === 'knowledge' }]" @click="viewMode = 'knowledge'">📚 知识库</button>
        <button :class="['view-tab', { active: viewMode === 'evaluator' }]" @click="viewMode = 'evaluator'">📊 评测中心</button>
      </div>

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
