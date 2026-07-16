<script setup>
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import { animate } from "animejs";
import { fetchDashboardStats, fetchRecentActivities } from "./api.js";

import { Card, Button, Divider } from "animal-island-vue";
import PageHeader from "@/shared/components/PageHeader.vue";
import {
  IconDevice,
  IconFileCode,
  IconPlay,
  IconBrain,
  IconClock,
  IconAlertCircle,
} from "@/shared/icons/index.js";

import StatsCard from "./components/StatsCard.vue";
import TrendBarChart from "./components/TrendBarChart.vue";
import TaskResultPanel from "./components/TaskResultPanel.vue";
import QuickActions from "./components/QuickActions.vue";
import ModuleNavigator from "./components/ModuleNavigator.vue";
import ActivityTimeline from "./components/ActivityTimeline.vue";

const router = useRouter();
const loading = ref(true);
const refreshing = ref(false);

const stats = ref({
  devices: { online: 0, total: 0, trend: 0 },
  cases: { total: 0, enabled: 0, trend: 0 },
  elements: { total: 0, pages: 0, breakdown: [] },
  runs: { total: 0, active: 0, trend: 0 },
  agents: { total: 0, active: 0, trend: 0 },
  reports: { total: 0 },
});

const passRate = ref(0);
const executionChart = ref({
  labels: [],
  success: [],
  failed: [],
  new_cases: [],
});
const executionSummary = ref({ passed: 0, failed: 0, new_cases_week: 0 });
const recentTasks = ref([]);
const lastUpdated = ref("");
const systemStatus = ref("normal");
const activities = ref([]);

const quickActions = computed(() => [
  { label: "新建用例", action: () => router.push("/cases/new") },
  { label: "执行测试", action: () => router.push("/runner") },
  { label: "元素截图", action: () => router.push("/elements") },
  { label: "AI 对话", action: () => router.push("/ai-assistant") },
  { label: "查看报告", action: () => router.push("/reports") },
]);

async function loadData() {
  loading.value = true;
  try {
    const [statsRes, activitiesRes] = await Promise.allSettled([
      fetchDashboardStats(),
      fetchRecentActivities(),
    ]);
    if (statsRes.status === "fulfilled" && statsRes.value.data?.ok) {
      const d = statsRes.value.data.data;
      stats.value = {
        devices: {
          online: d.devices?.online ?? 0,
          total: d.devices?.total ?? 0,
          trend: d.devices?.trend ?? 0,
        },
        cases: {
          total: d.cases?.total ?? 0,
          enabled: d.cases?.enabled ?? 0,
          trend: d.cases?.trend ?? 0,
        },
        elements: {
          total: d.elements?.total ?? 0,
          pages: d.elements?.pages ?? 0,
          breakdown: d.elements?.breakdown ?? [],
        },
        runs: {
          total: d.runs?.total ?? 0,
          active: d.runs?.active ?? 0,
          trend: d.runs?.trend ?? 0,
        },
        agents: {
          total: d.agents?.total ?? 0,
          active: d.agents?.active ?? 0,
          trend: d.agents?.trend ?? 0,
        },
        reports: { total: d.reports?.total ?? 0 },
      };
      passRate.value = d.pass_rate ?? 0;
      executionChart.value = d.charts?.execution ?? {
        labels: [],
        success: [],
        failed: [],
        new_cases: [],
      };
      executionSummary.value = d.execution_summary ?? {
        passed: 0,
        failed: 0,
        new_cases_week: 0,
      };
      recentTasks.value = d.recent_tasks ?? [];
      lastUpdated.value = d.last_updated ?? "";
      systemStatus.value = d.system_status ?? "normal";
    }
    if (activitiesRes.status === "fulfilled" && activitiesRes.value.data?.ok) {
      activities.value = activitiesRes.value.data.data || [];
    }
  } catch {}
  loading.value = false;
}

async function refreshData() {
  refreshing.value = true;
  try {
    const { data } = await fetchDashboardStats();
    if (data.ok) {
      const d = data.data;
      stats.value = {
        devices: {
          online: d.devices?.online ?? 0,
          total: d.devices?.total ?? 0,
          trend: d.devices?.trend ?? 0,
        },
        cases: {
          total: d.cases?.total ?? 0,
          enabled: d.cases?.enabled ?? 0,
          trend: d.cases?.trend ?? 0,
        },
        elements: {
          total: d.elements?.total ?? 0,
          pages: d.elements?.pages ?? 0,
          breakdown: d.elements?.breakdown ?? [],
        },
        runs: {
          total: d.runs?.total ?? 0,
          active: d.runs?.active ?? 0,
          trend: d.runs?.trend ?? 0,
        },
        agents: {
          total: d.agents?.total ?? 0,
          active: d.agents?.active ?? 0,
          trend: d.agents?.trend ?? 0,
        },
        reports: { total: d.reports?.total ?? 0 },
      };
      passRate.value = d.pass_rate ?? 0;
      executionChart.value = d.charts?.execution ?? {
        labels: [],
        success: [],
        failed: [],
        new_cases: [],
      };
      executionSummary.value = d.execution_summary ?? {
        passed: 0,
        failed: 0,
        new_cases_week: 0,
      };
      recentTasks.value = d.recent_tasks ?? [];
      lastUpdated.value = d.last_updated ?? "";
      systemStatus.value = d.system_status ?? "normal";
    }
  } catch {}
  refreshing.value = false;
}

onMounted(() => {
  loadData();
});
</script>

<template>
  <div class="doc-page">
    <PageHeader
      title="仪表盘 Dashboard"
      subtitle="自动化测试平台 · 实时监控设备状态、用例执行、AI Agent 与测试报告"
      color="app-yellow"
    />

    <!-- 内容区 -->
    <div class="doc-body">
      <!-- 统计概览 -->
      <section class="doc-section">
        <div class="doc-section__header">
          <h3 class="doc-section__title">
            统计概览
            <span class="doc-tag">Overview</span>
          </h3>
          <Button
            type="default"
            size="small"
            :loading="refreshing"
            @click="refreshData"
            >刷新</Button
          >
        </div>
        <div class="doc-section__label">核心指标实时展示</div>
        <div class="dashboard__stats-grid">
          <StatsCard
            label="在线设备"
            :value="stats.devices.online"
            :suffix="` / ${stats.devices.total}`"
            color="app-green"
            pattern="app-green"
            :trend="stats.devices.trend"
            trend-label="近期活跃"
            :loading="loading"
          >
            <template #icon>
              <IconDevice :size="22" color="#6fba2c" />
            </template>
          </StatsCard>
          <StatsCard
            label="测试用例"
            :value="stats.cases.total"
            color="app-blue"
            pattern="app-blue"
            :trend="stats.cases.trend"
            trend-label="本周新增"
            :loading="loading"
          >
            <template #icon>
              <IconFileCode :size="22" color="#889df0" />
            </template>
          </StatsCard>
          <StatsCard
            label="活跃智能体"
            :value="stats.agents.active"
            suffix=""
            color="app-yellow"
            pattern="app-yellow"
            :trend="stats.agents.trend"
            :loading="loading"
          >
            <template #icon>
              <IconBrain :size="22" color="#f7cd67" />
            </template>
          </StatsCard>
          <StatsCard
            label="运行中任务"
            :value="stats.runs.active"
            suffix=""
            color="app-pink"
            pattern="app-pink"
            :trend="stats.runs.trend"
            :loading="loading"
          >
            <template #icon>
              <IconPlay :size="22" color="#f8a6b2" />
              <span
                class="dashboard__live-dot"
                v-if="stats.runs.active > 0"
              ></span>
            </template>
          </StatsCard>
        </div>
      </section>

      <!-- 趋势图表 -->
      <section class="doc-section">
        <h3 class="doc-section__title">
          趋势数据
          <span class="doc-tag">Trends</span>
        </h3>
        <div class="doc-section__label">
          近 12 期执行成功、失败与新建用例统计
        </div>
        <div class="dashboard__trends">
          <Card color="app-green" pattern="app-green" class="trends-chart-card">
            <TrendBarChart :chart="executionChart" />
          </Card>
          <Card color="app-blue" pattern="app-blue" class="trends-tasks-card">
            <div class="trends-tasks-card__title">任务执行结果</div>
            <TaskResultPanel :tasks="recentTasks" :summary="executionSummary" />
          </Card>
        </div>
      </section>

      <!-- 快捷操作 -->
      <section class="doc-section">
        <h3 class="doc-section__title">
          快捷操作
          <span class="doc-tag">Actions</span>
        </h3>
        <div class="doc-section__label">常用入口一键直达</div>
        <QuickActions
          :actions="quickActions"
          @action="(act) => act.action?.()"
        />
      </section>

      <!-- 功能模块 -->
      <section class="doc-section">
        <ModuleNavigator :stats="stats" />
      </section>

      <!-- 最近动态 -->
      <section class="doc-section">
        <h3 class="doc-section__title">
          最近动态
          <span class="doc-tag">Activity</span>
        </h3>
        <ActivityTimeline :items="activities" />
      </section>

      <!-- 页脚信息 -->
      <footer class="dashboard__footer">
        <div class="dashboard__footer-item">
          <IconClock :size="14" />
          <span>最近更新: {{ lastUpdated || "暂无数据" }}</span>
        </div>
        <div class="dashboard__footer-item">
          <IconAlertCircle :size="14" />
          <span
            >系统状态:
            {{ systemStatus === "normal" ? "正常运行" : "无设备连接" }}</span
          >
        </div>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.doc-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.doc-body {
  flex: 1;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
}

/* Stats grid */
.dashboard__stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}

@media (max-width: 900px) {
  .dashboard__stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (max-width: 480px) {
  .dashboard__stats-grid {
    grid-template-columns: 1fr;
  }
}

/* Trends */
.dashboard__trends {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 16px;
  align-items: stretch;
}

@media (max-width: 960px) {
  .dashboard__trends {
    grid-template-columns: 1fr;
  }
}

.trends-chart-card,
.trends-tasks-card {
  display: flex;
  flex-direction: column;
}

.trends-chart-card :deep(.animal-card__content),
.trends-tasks-card :deep(.animal-card__content) {
  padding: 18px;
  border-radius: 16px;
  background: rgba(255, 248, 240, 0.85);
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.trends-tasks-card__title {
  font-size: 13px;
  font-weight: 700;
  color: #725d42;
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

/* Live dot */
.dashboard__live-dot {
  position: absolute;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ef4444;
  top: -2px;
  right: -2px;
  animation: livePulse 1.5s ease-in-out infinite;
}
@keyframes livePulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.5);
  }
  50% {
    box-shadow: 0 0 0 6px rgba(239, 68, 68, 0);
  }
}

/* Footer */
.dashboard__footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  padding-top: 8px;
  color: #9f927d;
}

.dashboard__footer-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}
</style>
