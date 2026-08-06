<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import AppTabs from '@/shared/components/AppTabs.vue'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'
import WbLoader from './components/WbLoader.vue'
import AgentStickyNote from './components/AgentStickyNote.vue'
import TaskStickyNote from './components/TaskStickyNote.vue'
import KnowledgeBase from './KnowledgeBase.vue'
import EvaluatorTab from './EvaluatorTab.vue'
import ToolboxPanel from './components/ToolboxPanel.vue'
import { useAgentBoard } from './index.logic'
import { agentDetailRoute } from './constants'

const router = useRouter()
const dutyRosterRef = ref<HTMLElement | null>(null)
const {
  viewMode, agents, loading, testingId, confirmingId, healthResults, pendingModels,
  tasks, tasksLoading, activeTaskFilter, taskFilterAppTabs, filteredTasks,
  PAGE_HEADER, noteRotation, tapeHue, taskRotation, taskTapeHue,
  agentStatusClass, agentStatusText, getModelOptions,
  loadAgents, loadTasks, confirmModel, deleteAgent, testConnection,
  openAgent, editAgent, openTask, onAgentCardClick,
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
        <div ref="dutyRosterRef" class="dot-board duty-roster" v-loading="loading">
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

      <section class="doc-section task-section">
        <div class="doc-section__header">
          <h3 class="doc-section__title">任务看板<span class="doc-tag">Tasks</span></h3>
          <span class="filter-count">{{ filteredTasks.length }} / {{ tasks.length }}</span>
        </div>
        <div class="filter-bar">
          <AppTabs class="task-tabs" :items="taskFilterAppTabs" v-model="activeTaskFilter" :leaf-animation="true" :shadow="true">
            <template v-for="tab in taskFilterAppTabs" #[tab.key] :key="tab.key">
              <div class="dot-board task-board" v-loading="tasksLoading">
                <div v-if="tasksLoading && !filteredTasks.length" class="ai-loading-wrap">
                  <WbLoader /><span>正在加载任务…</span>
                </div>
                <TaskStickyNote
                  v-for="t in filteredTasks" :key="t.run_id" :task="t"
                  :rotation="taskRotation(t)" :tape-hue="taskTapeHue(t)" @open="openTask"
                />
                <EmptyState v-if="!filteredTasks.length && !tasksLoading" icon="📋"
                  :text="activeTaskFilter === 'all' ? '还没有 AI 任务' : '当前状态下没有任务便签'"
                  :hint="activeTaskFilter === 'all' ? '在对话里让智能体帮你创建任务' : '尝试切换筛选条件'" />
              </div>
            </template>
          </AppTabs>
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
