<script setup>
import { ref, onMounted } from "vue";
import { animate } from "animejs";
import { fetchDashboardStats, fetchRecentActivities } from "./api.js";

// Card, Divider → el-card, el-divider (Element Plus auto-import)
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue";
import {
  IconDevice,
  IconFileCode,
  IconPlay,
  IconBrain,
  IconClock,
  IconAlertCircle,
} from "@/shared/icons/index.js";

import StatsAppCard from "./components/StatsCard.vue";
import TrendBarChart from "./components/TrendBarChart.vue";
import TaskResultPanel from "./components/TaskResultPanel.vue";
import ModuleNavigator from "./components/ModuleNavigator.vue";
import ActivityTimeline from "./components/ActivityTimeline.vue";

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
  refreshing.value = false;
}

onMounted(() => {
  loadData();
});
</script>

<template>
  <div class="doc-page wb-shell">
    <WorkbenchHeader
      title="仪表盘"
      subtitle="自动化测试平台 · 实时监控设备状态、用例执行、AI Agent 与测试报告"
      icon="layout-dashboard"
      icon-gradient="linear-gradient(135deg,#F4D35E,#f0c06a)"
    >
      <template #actions>
        <el-button class="wb-btn wb-btn--sunset" size="small" :loading="refreshing" @click="refreshData">
          刷新
        </el-button>
      </template>
    </WorkbenchHeader>

    <!-- 内容区 -->
    <div class="doc-body">
      <!-- 统计概览 -->
      <section class="doc-section">
        <div class="doc-section__header">
          <h3 class="doc-section__title">
            统计概览
            <span class="doc-tag">Overview</span>
          </h3>
        </div>
        <div class="doc-section__label">核心指标实时展示</div>
        <div class="dashboard__stats-grid">
          <StatsAppCard
            label="在线设备"
            desc="ADB 扫描 · 连接锁定 · 排队调度"
            :value="stats.devices.online"
            :suffix="` / ${stats.devices.total}`"
            color="app-green"
            :trend="stats.devices.trend"
            trend-label="近期活跃"
            path="/devices"
            :loading="loading"
          >
            <template #icon>
              <IconDevice :size="22" color="#fff" />
            </template>
          </StatsAppCard>
          <StatsAppCard
            label="测试用例"
            desc="步骤编排 · 目录树 · YAML 导入导出"
            :value="stats.cases.total"
            color="app-teal"
            :trend="stats.cases.trend"
            trend-label="本周新增"
            path="/cases"
            :loading="loading"
          >
            <template #icon>
              <IconFileCode :size="22" color="#fff" />
            </template>
          </StatsAppCard>
          <StatsAppCard
            label="活跃智能体"
            desc="自然语言驱动 · SSE 流式 · 知识库"
            :value="stats.agents.active"
            color="app-blue"
            :trend="stats.agents.trend"
            trend-label="智能体"
            path="/ai-assistant"
            :loading="loading"
          >
            <template #icon>
              <IconBrain :size="22" color="#fff" />
            </template>
          </StatsAppCard>
          <StatsAppCard
            label="运行中任务"
            desc="任务调度 · 实时进度 · WebSocket 日志"
            :value="stats.runs.active"
            color="app-pink"
            :trend="stats.runs.trend"
            trend-label="执行中"
            path="/runner"
            :loading="loading"
          >
            <template #icon>
              <IconPlay :size="22" color="#fff" />
              <span
                class="dashboard__live-dot"
                v-if="stats.runs.active > 0"
              ></span>
            </template>
          </StatsAppCard>
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
          <el-card class="trends-chart-card">
            <TrendBarChart :chart="executionChart" />
          </el-card>
          <el-card class="trends-tasks-card">
            <div class="trends-tasks-card__title">任务执行结果</div>
            <TaskResultPanel :tasks="recentTasks" :summary="executionSummary" />
          </el-card>
        </div>
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

/* Stats grid — 对齐参考图模块卡片风格 */
.dashboard__stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

@media (max-width: 1100px) {
  .dashboard__stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (max-width: 520px) {
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

.trends-chart-card :deep(.el-card__body),
.trends-tasks-card :deep(.el-card__body) {
  padding: 18px;
  border-radius: 16px;
  background: var(--app-glass-card, rgba(255,255,255,0.65));
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.trends-tasks-card__title {
  font-size: 13px;
  font-weight: 700;
  color: var(--app-text, #4a4e69);
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
  background: #fff;
  border: 2px solid #f87171;
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
