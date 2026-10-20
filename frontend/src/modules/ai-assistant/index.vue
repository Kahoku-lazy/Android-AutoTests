<script setup lang="ts">
import { ref, computed } from "vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import WbLoader from "./components/WbLoader.vue"
import AgentRouteCard from "./components/AgentRouteCard.vue"
import TaskBoard from "./components/TaskBoard.vue"
import { displayedAssistantCards } from "./helpers/assistant-cards"
import { useAgentBoard } from "./index.logic"
import { useAuthUser } from "@/shared/composables/useAuthUser"

const dutyRosterRef = ref<HTMLElement | null>(null)
const { agents, loading, agentsError, PAGE_HEADER, loadAgents, editAgent } =
  useAgentBoard(dutyRosterRef)

const { isSuperuser } = useAuthUser()
const isAdmin = computed(() => isSuperuser.value === true)

// 两条助手线路（每条线路独立 name/avatar，存于 route_configs）
const routeCards = computed(() =>
  displayedAssistantCards(agents.value[0]).map((card) => ({
    key: card.key,
    config: card.config,
    agentName: card.name,
    agentAvatar: card.avatar,
  })),
)

// ── 视图（AI 助手只有一个入口：平台小助手看板 + 任务列表）──
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell ai-workbench">
    <WorkbenchHeader
      title="平台小助手"
      subtitle="助手看板 + 任务卡片列表：配置两条线路、新建任务并下发执行"
      :icon="PAGE_HEADER.icon"
      :icon-gradient="PAGE_HEADER.iconGradient"
    />

    <div class="doc-body">
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
            v-for="rc in routeCards"
            :key="rc.key"
            :config="rc.config"
            :agent-name="rc.agentName"
            :agent-avatar="rc.agentAvatar"
            :can-manage="isAdmin"
            @edit="editAgent(agents[0]?.id ?? 0, rc.key)"
          />
          <EmptyState
            v-if="!agents.length && !loading"
            icon="🤖"
            text="还没有智能体"
            :hint="'请联系管理员配置智能体'"
          />
        </div>
      </section>

      <!-- 模块 2：任务卡片列表（新建任务弹窗 + 卡片式列表） -->
      <TaskBoard />
    </div>
  </div>
</template>

<style src="./index.style.css" scoped></style>

<style scoped>
.route-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 220px), max-content));
  gap: var(--app-space-md);
  align-items: start;
  justify-items: start;
}
</style>
