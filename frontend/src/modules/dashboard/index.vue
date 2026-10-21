<script setup lang="ts">
import { useDashboardView, toMillions } from "./DashboardView.logic"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import StatsAppCard from "./components/StatsCard.vue"
import AppCard from "@/shared/components/AppCard.vue"
import { sketchToneAt, sketchTiltAt } from "@/shared/helpers/sketchCard"
import TrendBarChart from "./components/TrendBarChart.vue"
import SeriesBarChart from "./components/SeriesBarChart.vue"
import TodayUsageChart from "./components/TodayUsageChart.vue"
import { useMidnightRefresh } from "./composables/useMidnightRefresh"
import TaskResultPanel from "./components/TaskResultPanel.vue"
import ActivityTimeline from "./components/ActivityTimeline.vue"
import {
  IconDevice,
  IconPlay,
  IconBrain,
  IconClock,
  IconAlertCircle,
  IconLayers,
  IconMonitor,
  IconTarget,
  IconTrendingUp,
  IconActivity,
  IconZap,
} from "@/shared/icons/index"

const {
  loading,
  refreshing,
  error,
  PAGE_HEADER,
  stats,
  executionChart,
  executionSummary,
  aiTokenChart,
  deepseekCostChart,
  recentTasks,
  lastUpdated,
  systemStatus,
  activities,
  loadData,
  refreshData,
  caseProjectCards,
  tokenSeries,
  costSeries,
  todayUsageSeries,
} = useDashboardView()

// 跨零点自动换天：刷新后「今日」系列与三张按日图都切到新的一天
useMidnightRefresh(refreshData)
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell dashboard-workbench">
    <WorkbenchHeader
      :title="PAGE_HEADER.title"
      :subtitle="PAGE_HEADER.subtitle"
      :icon="PAGE_HEADER.icon"
      :icon-gradient="PAGE_HEADER.iconGradient"
    >
      <template #actions>
        <el-button
          class="wb-btn wb-btn--sunset"
          size="small"
          :loading="refreshing"
          @click="refreshData"
        >
          刷新
        </el-button>
      </template>
    </WorkbenchHeader>

    <ErrorState v-if="error" :message="error" @retry="loadData" />

    <div class="doc-body">
      <!-- ① 平台运营 -->
      <section class="doc-section doc-section--board ch-ops">
        <header class="chapter-head">
          <div class="chapter-head__left">
            <div class="chapter-mark"><IconMonitor :size="16" /></div>
            <div>
              <div class="chapter-eyebrow">Platform Ops</div>
              <h3 class="chapter-title"><span class="marker">平台运营</span></h3>
              <p class="chapter-desc">核心入口指标 · 实时状态可点进模块</p>
            </div>
          </div>
        </header>
        <div class="dashboard__stats-grid">
          <StatsAppCard
            label="在线设备"
            :value="stats.devices.online"
            color="sage"
            path="/devices"
            :loading="loading"
          >
            <template #icon><IconDevice :size="15" /></template>
          </StatsAppCard>
          <StatsAppCard
            label="活跃智能体"
            :value="stats.agents.active"
            color="gray"
            path="/ai-assistant"
            :loading="loading"
          >
            <template #icon><IconBrain :size="15" /></template>
          </StatsAppCard>
          <StatsAppCard
            label="运行中任务"
            :value="stats.runs.active"
            color="rose"
            path="/reports"
            :loading="loading"
            :live="stats.runs.active > 0"
          >
            <template #icon><IconPlay :size="15" /></template>
          </StatsAppCard>
          <StatsAppCard
            label="任务数量"
            :value="stats.aiUsage.taskCount.total"
            color="gray"
            path="/tasks"
            :loading="loading"
            :desc="`今日 ${stats.aiUsage.taskCount.today.toLocaleString()}`"
          >
            <template #icon><IconBrain :size="15" /></template>
          </StatsAppCard>
          <StatsAppCard
            label="工作流"
            :value="stats.workflow.total"
            color="pale"
            path="/workflow"
            :loading="loading"
          >
            <template #icon><IconLayers :size="15" /></template>
          </StatsAppCard>
        </div>
      </section>

      <!-- ② AI 用量 -->
      <section class="doc-section doc-section--board ch-ai">
        <header class="chapter-head">
          <div class="chapter-head__left">
            <div class="chapter-mark"><IconBrain :size="16" /></div>
            <div>
              <div class="chapter-eyebrow">AI Usage</div>
              <h3 class="chapter-title"><span class="marker">AI 用量</span></h3>
              <p class="chapter-desc">Token · 缓存 · DeepSeek 费用</p>
            </div>
          </div>
        </header>
        <div class="ch-ai__body" :class="{ 'ch-ai__body--solo': !stats.aiUsage.agents.length }">
          <div class="ai-usage-kpis">
            <StatsAppCard
              label="累计用量"
              :value="toMillions(stats.aiUsage.totalTokens.total)"
              suffix="M"
              :decimals="2"
              color="sage"
              :loading="loading"
              desc="DeepSeek"
            >
              <template #icon><IconTrendingUp :size="15" /></template>
            </StatsAppCard>
            <StatsAppCard
              label="当天用量"
              :value="toMillions(stats.aiUsage.totalTokens.today)"
              suffix="M"
              :decimals="2"
              color="cream"
              :loading="loading"
              desc="DeepSeek"
            >
              <template #icon><IconLayers :size="15" /></template>
            </StatsAppCard>
            <StatsAppCard
              label="缓存命中率"
              :value="stats.aiUsage.cacheHitRate.total"
              suffix="%"
              :decimals="1"
              color="deep"
              :loading="loading"
              desc="DeepSeek"
            >
              <template #icon><IconTarget :size="15" /></template>
            </StatsAppCard>
            <StatsAppCard
              label="总费用"
              :value="stats.aiUsage.deepseekCost.total"
              suffix=" 元"
              :significant-digits="3"
              color="dust"
              :loading="loading"
              desc="DeepSeek"
            >
              <template #icon><IconZap :size="15" /></template>
            </StatsAppCard>
            <StatsAppCard
              label="当天费用"
              :value="stats.aiUsage.deepseekCost.today"
              suffix=" 元"
              :significant-digits="3"
              color="dust"
              :loading="loading"
              desc="DeepSeek"
            >
              <template #icon><IconClock :size="15" /></template>
            </StatsAppCard>
          </div>
          <div v-if="stats.aiUsage.agents.length" class="agent-usage-list">
            <AppCard
              v-for="(agent, index) in stats.aiUsage.agents"
              :key="agent.id"
              class="agent-usage-card"
              :tone="sketchToneAt(index)"
              :tilt="sketchTiltAt(index)"
            >
              <h4 class="agent-usage-card__name">{{ agent.name || "智能体" }}</h4>
              <ul class="agent-usage-card__stats">
                <li>
                  <span>缓存命中</span><b>{{ agent.cache_hit_tokens.toLocaleString() }}</b>
                </li>
                <li>
                  <span>输入</span><b>{{ agent.input_tokens.toLocaleString() }}</b>
                </li>
                <li>
                  <span>输出</span><b>{{ agent.output_tokens.toLocaleString() }}</b>
                </li>
                <li>
                  <span>总费用</span><b>{{ agent.cost_total }} 元</b>
                </li>
              </ul>
            </AppCard>
          </div>
        </div>
      </section>

      <!-- ③ 测试资产：用例 + 元素 -->
      <section class="doc-section doc-section--board ch-asset">
        <header class="chapter-head">
          <div class="chapter-head__left">
            <div class="chapter-mark"><IconLayers :size="16" /></div>
            <div>
              <div class="chapter-eyebrow">Test Assets</div>
              <h3 class="chapter-title"><span class="marker">测试资产</span></h3>
              <p class="chapter-desc">用例库 + 元素库 · 同一存量视角</p>
            </div>
          </div>
          <div class="chip-row">
            <span class="chip chip--teal"
              >用例 <b>{{ stats.cases.total }}</b></span
            >
          </div>
        </header>
        <div class="asset-cols">
          <div>
            <div class="subhead">测试用例 <span class="subhead__tag">Cases</span></div>
            <div v-if="caseProjectCards.length" class="dashboard__stats-grid">
              <StatsAppCard
                v-for="item in caseProjectCards"
                :key="item.projectId"
                :label="item.name"
                :value="item.total"
                :color="item.color"
                :path="item.path"
                :loading="loading"
              >
                <template #icon>
                  <IconLayers :size="15" />
                </template>
              </StatsAppCard>
            </div>
            <div v-else-if="!loading" class="cases-empty">
              <p class="cases-empty__text">暂无用例项目</p>
              <RouterLink class="cases-empty__link" to="/cases">前往用例管理创建</RouterLink>
            </div>
          </div>
        </div>
      </section>

      <!-- ④ 趋势与动态 -->
      <section class="doc-section doc-section--board ch-trend">
        <header class="chapter-head">
          <div class="chapter-head__left">
            <div class="chapter-mark"><IconActivity :size="16" /></div>
            <div>
              <div class="chapter-eyebrow">Trends &amp; Activity</div>
              <h3 class="chapter-title"><span class="marker">趋势与动态</span></h3>
              <p class="chapter-desc">近 7 日任务卡 · Token · 费用 · 今日进度 · 活动流</p>
            </div>
          </div>
        </header>

        <div class="dashboard__trends">
          <AppCard class="trends-chart-card" :tone="sketchToneAt(0)" :tilt="sketchTiltAt(0)">
            <div class="trends-tasks-card__title">助手任务卡</div>
            <TrendBarChart :chart="executionChart" />
          </AppCard>
          <AppCard class="trends-tasks-card" :tone="sketchToneAt(1)" :tilt="sketchTiltAt(1)">
            <div class="trends-tasks-card__title">任务执行结果</div>
            <TaskResultPanel :tasks="recentTasks" :summary="executionSummary" />
          </AppCard>
        </div>
        <div class="dashboard__trends dashboard__trends--ai">
          <AppCard class="trends-chart-card" :tone="sketchToneAt(2)" :tilt="sketchTiltAt(2)">
            <div class="trends-tasks-card__title">每日 Token 用量</div>
            <SeriesBarChart :labels="aiTokenChart.labels" :series="tokenSeries" />
          </AppCard>
          <AppCard class="trends-chart-card" :tone="sketchToneAt(3)" :tilt="sketchTiltAt(3)">
            <div class="trends-tasks-card__title">每日 DeepSeek 费用（元）</div>
            <SeriesBarChart :labels="deepseekCostChart.labels" :series="costSeries" />
          </AppCard>
        </div>
        <div class="dashboard__trends dashboard__trends--single">
          <AppCard class="trends-chart-card" :tone="sketchToneAt(4)" :tilt="sketchTiltAt(4)">
            <div class="trends-tasks-card__title">今日 Token 与费用（逐小时）</div>
            <TodayUsageChart :series="todayUsageSeries" />
          </AppCard>
        </div>

        <div class="subhead">最近动态 <span class="subhead__tag">Activity</span></div>
        <ActivityTimeline :items="activities" />
      </section>

      <footer class="dashboard__footer">
        <div class="dashboard__footer-item">
          <IconClock :size="14" />
          <span>最近更新: {{ lastUpdated || "暂无数据" }}</span>
        </div>
        <div class="dashboard__footer-item">
          <IconAlertCircle :size="14" />
          <span>系统状态: {{ systemStatus === "normal" ? "正常运行" : "无设备连接" }}</span>
        </div>
      </footer>
    </div>
  </div>
</template>

<style src="./DashboardView.style.css" scoped></style>
<style scoped>
.agent-usage-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--app-space-md);
  margin-top: 0;
}

@media (max-width: 1100px) {
  .agent-usage-list {
    margin-top: var(--app-space-md);
  }
}

.agent-usage-card {
  height: 100%;
}

.agent-usage-card :deep(.el-card__body) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.agent-usage-card__name {
  margin: 0 0 var(--app-space-sm);
  font-size: var(--app-size-md);
}

.agent-usage-card__stats {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  align-content: center;
  gap: var(--app-space-sm);
  margin: 0;
  padding: 0;
  list-style: none;
}

.agent-usage-card__stats li {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-xs);
  font-size: var(--app-size-sm);
}

.agent-usage-card__stats span {
  color: var(--app-text-secondary);
  font-size: var(--app-size-xs);
}
</style>
