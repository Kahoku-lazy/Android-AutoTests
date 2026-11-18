/**
 * [P0] 必测 — 日志关键词面板（spec: device-log-keyword-catalog）
 *
 * 目录：tests/serial-log/p0/
 * 断言：① 四列表格（含范围）+ 行数/计数、数据库来源与刷新时效标注；② 搜索过滤；
 * ③ 范围筛选与搜索叠加、计数恒全量；④ 空表给可读空态；⑤ 面板内没有任何写控件（只读）。
 *
 * AppTable 在本用例里以桩件呈现（只把 columns / data-source 渲染出来），
 * 断的是本面板的列定义与数据口径，不是 el-table 自身行为。
 */
import { beforeEach, describe, expect, it, vi } from "vitest"
import { mount } from "@vue/test-utils"
import { nextTick } from "vue"
import ElementPlus from "element-plus"

const fetchKeywords = vi.fn()

vi.mock("@/modules/serial-log/api", () => ({
  fetchLogKeywords: (...args: unknown[]) => fetchKeywords(...args),
}))

import LogKeywordPanel from "@/modules/serial-log/components/LogKeywordPanel.vue"

const CATALOG = {
  keywords: [
    {
      keyword: "switch_on",
      features: [{ id: 0, module: "设备开关", feature: "打开设备成功", scope: "*" }],
    },
    {
      keyword: "switch_off",
      features: [{ id: 1, module: "设备开关", feature: "关闭设备成功", scope: "*" }],
    },
    {
      keyword: "color_configs_set_success",
      features: [
        { id: 2, module: "音效律动", feature: "灯光颜色设置成功", scope: "*" },
        { id: 17, module: "彩色模式", feature: "手动-颜色设置成功", scope: "*" },
      ],
    },
    {
      keyword: "h6601_boot",
      features: [{ id: 56, module: "设备开关", feature: "H6601开机完成", scope: "H6601" }],
    },
  ],
  keyword_count: 4,
  feature_count: 5,
  origin: "db",
  updated_at: "2026-11-18 12:00:00",
  note: "",
}

const stubs = {
  EmptyState: {
    props: ["icon", "text", "hint"],
    template: '<div class="stub-empty">{{ text }}|{{ hint }}</div>',
  },
  ErrorState: { props: ["message"], template: '<div class="stub-error">{{ message }}</div>' },
  SkeletonCard: { template: '<div class="stub-skeleton" />' },
  AppTable: {
    props: ["columns", "dataSource"],
    template:
      '<div class="stub-table" :data-rows="dataSource.length" data-testid="log-keyword-table">' +
      '<span class="stub-cols">{{ columns.map((c) => c.title || c.label).join("/") }}</span>' +
      '<span v-for="row in dataSource" :key="row.key" class="stub-row">' +
      "{{ row.keyword }}|{{ row.module }}|#{{ row.featureId }}|{{ row.featureName }}</span>" +
      "</div>",
  },
}

async function mountPanel() {
  // 搜索框已是 Element Plus 的 el-input：这里按需注册 EP，而不是给 el-input 造桩
  const wrapper = mount(LogKeywordPanel, { global: { stubs, plugins: [ElementPlus] } })
  await nextTick()
  await nextTick()
  return wrapper
}

describe("[P0] LogKeywordPanel", () => {
  beforeEach(() => {
    fetchKeywords.mockReset()
    fetchKeywords.mockResolvedValue({ status: true, data: CATALOG })
  })

  it("四列表格：列名齐全，一行一个「关键词 × 功能点 × 范围」", async () => {
    const wrapper = await mountPanel()
    const table = wrapper.find('[data-testid="log-keyword-table"]')
    expect(table.exists()).toBe(true)
    expect(table.find(".stub-cols").text()).toBe("功能点/功能模块/关键词/范围")
    expect(table.attributes("data-rows")).toBe("5")
    const rows = wrapper.findAll(".stub-row")
    expect(rows[0].text()).toBe("switch_on|设备开关|#0|打开设备成功")
    expect(rows.map((r) => r.text())).toContain(
      "color_configs_set_success|彩色模式|#17|手动-颜色设置成功",
    )
  })

  it("计数为关键词/功能点/行数", async () => {
    const wrapper = await mountPanel()
    const text = wrapper.find('[data-testid="log-keyword-count"]').text()
    expect(text).toContain("4 个关键词")
    expect(text).toContain("5 个功能点")
    expect(text).toContain("5 行")
  })

  it("标注数据库来源与刷新时效，不残留重启文案", async () => {
    const wrapper = await mountPanel()
    const origin = wrapper.find('[data-testid="log-keyword-origin"]').text()
    expect(origin).toContain("数据库关键词表")
    expect(origin).toContain("最近写入于 2026-11-18 12:00:00")
    expect(origin).toContain("刷新即取最新条目")
    expect(origin).not.toContain("重启")
  })

  it("搜索过滤表格行；计数仍报全量；清空后回到全量", async () => {
    const wrapper = await mountPanel()
    const input = wrapper.find('[data-testid="log-keyword-search"]')
    await input.setValue("彩色")
    expect(wrapper.find('[data-testid="log-keyword-table"]').attributes("data-rows")).toBe("1")
    expect(wrapper.find('[data-testid="log-keyword-count"]').text()).toContain("4 个关键词")
    await input.setValue("zzz")
    expect(wrapper.find('[data-testid="log-keyword-table"]').attributes("data-rows")).toBe("0")
    await input.setValue("")
    expect(wrapper.find('[data-testid="log-keyword-table"]').attributes("data-rows")).toBe("5")
  })

  it("范围筛选：只看 H6601 专用 / 通用；计数恒全量；与搜索叠加；恢复全部回全量", async () => {
    const wrapper = await mountPanel()
    const select = wrapper.findComponent('[data-testid="log-keyword-scope"]')
    await select.setValue("H6601")
    expect(wrapper.find('[data-testid="log-keyword-table"]').attributes("data-rows")).toBe("1")
    expect(wrapper.find('[data-testid="log-keyword-count"]').text()).toContain("4 个关键词")
    // 叠加搜索：H6601 范围内搜「开机」命中 1 行，搜「彩色」无命中
    const input = wrapper.find('[data-testid="log-keyword-search"]')
    await input.setValue("开机")
    expect(wrapper.find('[data-testid="log-keyword-table"]').attributes("data-rows")).toBe("1")
    await input.setValue("彩色")
    expect(wrapper.find('[data-testid="log-keyword-table"]').attributes("data-rows")).toBe("0")
    await input.setValue("")
    await select.setValue("*")
    expect(wrapper.find('[data-testid="log-keyword-table"]').attributes("data-rows")).toBe("4")
    await select.setValue("all")
    expect(wrapper.find('[data-testid="log-keyword-table"]').attributes("data-rows")).toBe("5")
  })

  it("表不可用时给可读空态（含后端说明），不渲染表格", async () => {
    fetchKeywords.mockResolvedValue({
      status: true,
      data: {
        ...CATALOG,
        keywords: [],
        keyword_count: 0,
        feature_count: 0,
        origin: "none",
        note: "关键词表不可用：未找到 /x.json",
      },
    })
    const wrapper = await mountPanel()
    expect(wrapper.find(".stub-empty").text()).toContain("关键词表不可用")
    expect(wrapper.find('[data-testid="log-keyword-table"]').exists()).toBe(false)
  })

  it("只读：正文里除搜索框与范围筛选外没有任何控件，页头只有刷新", async () => {
    const wrapper = await mountPanel()
    const body = wrapper.find('[data-testid="log-keyword-panel"]')
    expect(body.findAll("button").length).toBe(0)
    // 两个输入控件：搜索框 + 范围筛选下拉（均为读侧过滤，不是写入口）
    expect(body.findAll("input").length).toBe(2)
    expect(body.find('input[type="file"]').exists()).toBe(false)
    expect(body.text()).not.toContain("保存")
    expect(body.text()).not.toContain("删除")
    // 唯一的操作是页头「刷新」（重新拉取只读数据）
    expect(wrapper.findAll(".sl-cat-actions button").map((b) => b.text())).toEqual(["刷新"])
  })
})
