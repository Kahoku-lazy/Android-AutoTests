import { beforeEach, describe, expect, it, vi } from "vitest"
import { defineComponent, ref } from "vue"
import { createRouter, createMemoryHistory } from "vue-router"
import { mount } from "@vue/test-utils"
import DashboardView from "@/modules/dashboard/index.vue"

const operator = ref(false)

vi.mock("@/shared/composables/useAuthUser", () => ({
  useAuthUser: () => ({ isOperator: operator }),
}))

vi.mock("@/modules/dashboard/DashboardView.logic", () => ({
  toMillions: (value: number) => value,
  PAGE_HEADER: { title: "仪表盘", subtitle: "", icon: "layout-dashboard", iconGradient: "" },
  useDashboardView: () => ({
    loading: ref(false),
    error: ref(null),
    PAGE_HEADER: { title: "仪表盘", subtitle: "", icon: "layout-dashboard", iconGradient: "" },
    stats: ref({
      devices: { online: 2, total: 2 },
      cases: { total: 0, enabled: 0, breakdown: [] },
      assistants: { total: 3 },
      workflows: { total: 1 },
      runs: { active: 1, pending: 0 },
      ops: { users: 4, agents: 2, models: 5 },
      aiUsage: {
        taskCount: { today: 2, total: 9 },
        agents: [],
        cacheHitRate: { today: 0, total: 0 },
        totalTokens: { today: 0, total: 0 },
        deepseekCost: { today: 0, total: 0 },
        displayFx: { date: "2026-11-17", usdCny: "6.7132" },
      },
    }),
    executionChart: ref({ labels: [], success: [], failed: [] }),
    executionSummary: ref({ passed: 0, failed: 0 }),
    aiTokenChart: ref({
      labels: [],
      totalTokens: [],
      cacheTokens: [],
      byModel: [],
      voiceByModel: [],
    }),
    deepseekCostChart: ref({ labels: [], cost: [] }),
    recentTasks: ref([]),
    lastUpdated: ref(""),
    systemStatus: ref("normal"),
    activities: ref([]),
    caseProjectCards: ref([]),
    todayUsageSeries: ref([]),
    loadData: vi.fn(),
    refreshData: vi.fn(),
  }),
}))

vi.mock("@/modules/dashboard/composables/useMidnightRefresh", () => ({
  useMidnightRefresh: () => undefined,
}))

const Stub = defineComponent({ template: "<div><slot /></div>" })

function mountDashboard() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: "/:pathMatch(.*)*", component: Stub }],
  })
  return mount(DashboardView, {
    global: {
      plugins: [router],
      stubs: {
        WorkbenchHeader: Stub,
        ErrorState: Stub,
        AppCard: Stub,
        TrendBarChart: Stub,
        ModelLineChart: Stub,
        TodayUsageChart: Stub,
        TaskResultPanel: Stub,
        ActivityTimeline: Stub,
        PartNumber: Stub,
        RouterLink: Stub,
      },
    },
  })
}

describe("[P0] 平台概览卡片", () => {
  beforeEach(() => {
    operator.value = false
  })

  it("按顺序展示五张运行卡，排队为零也显示", () => {
    const text = mountDashboard().text()
    const labels = ["在线设备", "平台助手", "工作流", "运行中任务", "任务数量"]
    const positions = labels.map((label) => text.indexOf(label))
    expect(positions.every((position) => position >= 0)).toBe(true)
    expect([...positions].sort((a, b) => a - b)).toEqual(positions)
    expect(text).toContain("排队 0")
    expect(text).not.toContain("活跃智能体")
    expect(text).not.toContain("运营配置")
  })

  it("运营看到三张配置卡", () => {
    operator.value = true
    const text = mountDashboard().text()
    expect(text).toContain("运营配置")
    expect(text).toContain("用户管理")
    expect(text).toContain("Agent配置")
    expect(text).toContain("模型配置")
  })
})
