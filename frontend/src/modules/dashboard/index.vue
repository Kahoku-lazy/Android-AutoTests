<script setup lang="ts">
import { computed, ref } from "vue"
import { useDashboardView, toMillions } from "./DashboardView.logic"
import { useAuthUser } from "@/shared/composables/useAuthUser"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import StatsAppCard from "./components/StatsCard.vue"
import AppCard from "@/shared/components/AppCard.vue"
import { sketchToneAt, sketchTiltAt } from "@/shared/helpers/sketchCard"
import { formatSignificant } from "@/shared/animations"
import TrendBarChart from "./components/TrendBarChart.vue"
import ModelLineChart from "./components/ModelLineChart.vue"
import TodayUsageChart from "./components/TodayUsageChart.vue"
import { useMidnightRefresh } from "./composables/useMidnightRefresh"
import TaskResultPanel from "./components/TaskResultPanel.vue"
import ActivityTimeline from "./components/ActivityTimeline.vue"
import PartNumber from "./components/PartNumber.vue"
import {
  IconDevice,
  IconPlay,
  IconBrain,
  IconClock,
  IconAlertCircle,
  IconLayers,
  IconMonitor,
  IconTrendingUp,
  IconActivity,
} from "@/shared/icons/index"

const {
  loading,
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
  todayUsageSeries,
} = useDashboardView()

const { isOperator } = useAuthUser()
const currency = ref<"CNY" | "USD">("CNY")
const trendScope = ref<"all" | "voice">("all")
const fx = computed(() => Number(stats.value.aiUsage.displayFx.usdCny) || 6.7132)

function money(cny: number): string {
  if (currency.value === "USD") return formatSignificant(cny / fx.value, 3)
  return formatSignificant(cny, 3)
}

function moneyUnit(): string {
  return currency.value === "USD" ? "美元" : "元"
}

const modelSeries = computed(() => {
  const rows =
    trendScope.value === "voice" ? aiTokenChart.value.voiceByModel : aiTokenChart.value.byModel
  if (currency.value === "CNY") return rows
  return rows.map((row) => ({ ...row, cost: row.cost.map((value) => value / fx.value) }))
})

// 跨零点自动换天：刷新后「今日」系列与三张按日图都切到新的一天
useMidnightRefresh(refreshData)

/** Agent 用量卡顶点色条：按序号轮转模块色，与「卡片即零件」的编号卡一致 */
const AGENT_CARD_ACCENTS = ["var(--c-ai)", "var(--c-case)", "var(--c-runner)", "var(--c-workflow)"]

function agentCardAccent(index: number): string {
  return AGENT_CARD_ACCENTS[index % AGENT_CARD_ACCENTS.length]
}

/** Token 只允许 K / M 两个单位：数值与单位分开，便于单位用黑色、数值走渐变 */
function tokenValue(tokens: number): string {
  return tokens >= 1_000_000 ? (tokens / 1_000_000).toFixed(2) : (tokens / 1_000).toFixed(2)
}

function tokenUnit(tokens: number): string {
  return tokens >= 1_000_000 ? "M" : "K"
}
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell dashboard-workbench">
    <WorkbenchHeader
      :title="PAGE_HEADER.title"
      :subtitle="PAGE_HEADER.subtitle"
      :icon="PAGE_HEADER.icon"
      :icon-gradient="PAGE_HEADER.iconGradient"
    />

    <ErrorState v-if="error" :message="error" @retry="loadData" />

    <div class="doc-body">
      <!-- ① 平台概览：平台运行指标 + 测试用例资产 -->
      <section class="doc-section doc-section--board ch-ops">
        <header class="chapter-head">
          <div class="chapter-head__left">
            <div class="chapter-mark"><IconMonitor :size="16" /></div>
            <div>
              <h3 class="chapter-title"><span class="marker">平台概览</span></h3>
            </div>
          </div>
          <div class="chip-row">
            <span class="chip chip--teal"
              >用例 <b>{{ stats.cases.total }}</b></span
            >
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
            label="平台助手"
            :value="stats.assistants.total"
            color="gray"
            path="/ai-assistant"
            :loading="loading"
          >
            <template #icon><IconBrain :size="15" /></template>
          </StatsAppCard>
          <StatsAppCard
            label="工作流"
            :value="stats.workflows.total"
            color="gray"
            path="/ai-assistant"
            :loading="loading"
          >
            <template #icon><IconLayers :size="15" /></template>
          </StatsAppCard>
          <StatsAppCard
            label="运行中任务"
            :value="stats.runs.active"
            color="rose"
            path="/tasks"
            :loading="loading"
            :live="stats.runs.active > 0"
            :desc="`排队 ${stats.runs.pending.toLocaleString()}`"
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
        </div>

        <div v-if="isOperator && stats.ops" class="overview-assets">
          <div class="subhead">运营配置 <span class="subhead__tag">Ops</span></div>
          <div class="dashboard__stats-grid">
            <StatsAppCard
              label="用户管理"
              :value="stats.ops.users"
              color="gray"
              path="/ops/users"
              :loading="loading"
            >
              <template #icon><IconMonitor :size="15" /></template>
            </StatsAppCard>
            <StatsAppCard
              label="Agent配置"
              :value="stats.ops.agents"
              color="gray"
              path="/ops/agents"
              :loading="loading"
            >
              <template #icon><IconBrain :size="15" /></template>
            </StatsAppCard>
            <StatsAppCard
              label="模型配置"
              :value="stats.ops.models"
              color="gray"
              path="/ops/model-configs"
              :loading="loading"
            >
              <template #icon><IconLayers :size="15" /></template>
            </StatsAppCard>
          </div>
        </div>

        <div class="overview-assets">
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
      </section>

      <!-- ② AI 用量 -->
      <section class="doc-section doc-section--board ch-ai">
        <header class="chapter-head">
          <div class="chapter-head__left">
            <div class="chapter-mark"><IconBrain :size="16" /></div>
            <div>
              <h3 class="chapter-title"><span class="marker">AI 用量</span></h3>
            </div>
          </div>
        </header>
        <div class="ch-ai__body" :class="{ 'ch-ai__body--solo': !stats.aiUsage.agents.length }">
          <AppCard
            class="part-card ai-bill"
            :pin="false"
            :style="{ '--part-accent': 'var(--c-case)' }"
          >
            <div class="part-card__head">
              <PartNumber value="00" />
              <h4 class="part-card__title">平台账单</h4>
              <button
                type="button"
                class="part-card__stamp"
                @click="currency = currency === 'CNY' ? 'USD' : 'CNY'"
              >
                {{ currency === "CNY" ? "人民币" : "美元" }}
              </button>
            </div>
            <SkeletonCard v-if="loading" />
            <template v-else>
              <div class="part-card__hero">
                <span class="part-card__hero-label">缓存命中率</span>
                <strong class="part-card__hero-value"
                  >{{ stats.aiUsage.cacheHitRate.total.toFixed(1) }}<em>%</em></strong
                >
              </div>
              <div class="part-card__row">
                <div class="part-card__cell">
                  <span>当天用量</span>
                  <b>{{ toMillions(stats.aiUsage.totalTokens.today).toFixed(2) }}<em>M</em></b>
                </div>
                <div class="part-card__cell">
                  <span>当天费用</span>
                  <b
                    >{{ money(stats.aiUsage.deepseekCost.today) }}<em>{{ moneyUnit() }}</em></b
                  >
                </div>
              </div>
              <div class="part-card__row">
                <div class="part-card__cell">
                  <span>总用量</span>
                  <b>{{ toMillions(stats.aiUsage.totalTokens.total).toFixed(2) }}<em>M</em></b>
                </div>
                <div class="part-card__cell">
                  <span>总费用</span>
                  <b
                    >{{ money(stats.aiUsage.deepseekCost.total) }}<em>{{ moneyUnit() }}</em></b
                  >
                </div>
              </div>
            </template>
          </AppCard>
          <div v-if="stats.aiUsage.agents.length" class="agent-usage-list">
            <AppCard
              v-for="(agent, index) in stats.aiUsage.agents"
              :key="agent.id"
              class="part-card agent-usage-card"
              :pin="false"
              :style="{ '--part-accent': agentCardAccent(index) }"
            >
              <div class="part-card__head">
                <PartNumber :value="String(index + 1).padStart(2, '0')" />
                <h4 class="part-card__title">{{ agent.name || "智能体" }}</h4>
              </div>
              <div class="part-card__row">
                <div class="part-card__cell">
                  <span>缓存命中</span>
                  <b
                    >{{ tokenValue(agent.cache_hit_tokens)
                    }}<em>{{ tokenUnit(agent.cache_hit_tokens) }}</em></b
                  >
                </div>
                <div class="part-card__cell">
                  <span>输入</span>
                  <b
                    >{{ tokenValue(agent.input_tokens)
                    }}<em>{{ tokenUnit(agent.input_tokens) }}</em></b
                  >
                </div>
              </div>
              <div class="part-card__row">
                <div class="part-card__cell">
                  <span>输出</span>
                  <b
                    >{{ tokenValue(agent.output_tokens)
                    }}<em>{{ tokenUnit(agent.output_tokens) }}</em></b
                  >
                </div>
                <div class="part-card__cell">
                  <span>总费用</span>
                  <b>{{ formatSignificant(Number(agent.cost_total), 3) }}<em>元</em></b>
                </div>
              </div>
            </AppCard>
          </div>
        </div>

        <div class="ai-usage-trends">
          <div class="subhead">用量趋势 <span class="subhead__tag">Usage</span></div>
          <div class="dashboard__trends dashboard__trends--pair">
            <AppCard class="trends-chart-card" :tone="sketchToneAt(2)" :tilt="sketchTiltAt(2)">
              <div class="trends-tasks-card__title">近 7 日 Token 与费用</div>
              <div class="trend-scope">
                <button
                  type="button"
                  :class="{ active: trendScope === 'all' }"
                  @click="trendScope = 'all'"
                >
                  全部
                </button>
                <button
                  type="button"
                  :class="{ active: trendScope === 'voice' }"
                  @click="trendScope = 'voice'"
                >
                  Voice
                </button>
              </div>
              <ModelLineChart
                v-if="modelSeries.length"
                :labels="aiTokenChart.labels"
                :series="modelSeries"
                :unit="moneyUnit()"
              />
              <p v-else class="usage-empty">暂无用量</p>
            </AppCard>
            <AppCard class="trends-chart-card" :tone="sketchToneAt(3)" :tilt="sketchTiltAt(3)">
              <div class="trends-tasks-card__title">今日 Token 与费用</div>
              <TodayUsageChart :series="todayUsageSeries" />
            </AppCard>
          </div>
        </div>
      </section>

      <!-- ③ 趋势与动态 -->
      <section class="doc-section doc-section--board ch-trend">
        <header class="chapter-head">
          <div class="chapter-head__left">
            <div class="chapter-mark"><IconActivity :size="16" /></div>
            <div>
              <h3 class="chapter-title"><span class="marker">趋势与动态</span></h3>
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

        <div class="subhead">最近动态 <span class="subhead__tag">Activity</span></div>
        <ActivityTimeline :items="activities" />
      </section>
    </div>
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
</template>

<style src="./DashboardView.style.css" scoped></style>
<style scoped>
.agent-usage-list {
  display: grid;
  /* Agent-01 / Agent-02 横排；窄屏再回落成单列 */
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--app-space-md);
  margin-top: 0;
  align-items: stretch;
}

@media (max-width: 1400px) {
  .agent-usage-list {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 1100px) {
  .agent-usage-list {
    margin-top: var(--app-space-md);
  }
}

/* Agent 用量卡只声明布局；外壳（编号 / 色条 / 黄圆 / 分隔线）由 .part-card 提供 */
.agent-usage-card {
  height: 100%;
}
</style>
