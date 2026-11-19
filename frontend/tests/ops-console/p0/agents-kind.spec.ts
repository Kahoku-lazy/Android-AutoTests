/**
 * [P0] 必测 — Agent 配置「类型」列与保存契约（spec: ops-agent-config / ai-role-registry）
 *
 * 目录：tests/ops-console/p0/
 * 断言：① 「类型」列紧跟在「名称」后；② chip 三种状态（有类型 / 多值 / 未分类）；
 * ③ 草稿 ↔ 接口入参互转与提交前校验（未选类型被拦）。
 */
import { mount } from "@vue/test-utils"
import { describe, expect, it } from "vitest"
import OpsAgentKindTags from "@/modules/ops-console/components/OpsAgentKindTags.vue"
import { OPS_AGENT_COLUMNS } from "@/modules/ops-console/constants"
import {
  draftFromAgent,
  draftProblem,
  draftToInput,
  emptyDraft,
} from "@/modules/ops-console/helpers/agent-form"
import type { OpsAgent } from "@/modules/ops-console/types"

const agent: OpsAgent = {
  role_id: "20261118abc",
  name: "Android-UI-VERIFIER",
  model_config_id: 3,
  provider: "openai",
  api_key_env: "OPENAI_API_KEY",
  model_name: "deepseek-flash",
  base_url: "https://example.test/v1",
  api_protocol: "openai",
  system_prompt: "## 角色",
  kinds: ["verifier"],
}

describe("[P0] 类型列位置", () => {
  it("「类型」列紧跟在「名称」之后", () => {
    const labels = OPS_AGENT_COLUMNS.map((item) => item.label)
    expect(labels.slice(0, 2)).toEqual(["名称", "类型"])
    expect(OPS_AGENT_COLUMNS[1].prop).toBe("kinds")
  })

  it("列顺序保持名称 / 类型 / 模型配置 / 系统提示词 / 操作", () => {
    expect(OPS_AGENT_COLUMNS.map((item) => item.label)).toEqual([
      "名称",
      "类型",
      "模型配置",
      "系统提示词",
      "操作",
    ])
  })
})

describe("[P0] 类型标签渲染", () => {
  function tags(kinds: OpsAgent["kinds"]) {
    return mount(OpsAgentKindTags, { props: { kinds } })
  }

  it("单个类型显示中文标签", () => {
    const wrapper = tags(["executor"])
    expect(wrapper.text()).toContain("执行者")
    expect(wrapper.find(".ops-kind__unset").exists()).toBe(false)
  })

  it("多个类型逐个出 chip", () => {
    const wrapper = tags(["verifier", "planner"])
    expect(wrapper.findAll(".ops-kind__tag").map((node) => node.text())).toEqual([
      "验收者",
      "规划者",
    ])
  })

  it("空数组显示「未分类」", () => {
    const wrapper = tags([])
    expect(wrapper.text()).toContain("未分类")
    expect(wrapper.find(".ops-kind__tag").exists()).toBe(false)
  })

  it("未知取值按未分类兜底，不渲染空白 chip", () => {
    const wrapper = tags(["reviewer" as never])
    expect(wrapper.find(".ops-kind__tag").exists()).toBe(false)
    expect(wrapper.text()).toContain("未分类")
  })
})

describe("[P0] 草稿与入参", () => {
  it("新建草稿类型为空", () => {
    expect(emptyDraft().kind).toBe("")
  })

  it("编辑预填取后端 kinds 第一项", () => {
    expect(draftFromAgent(agent)).toEqual({
      name: "Android-UI-VERIFIER",
      model_config_id: 3,
      system_prompt: "## 角色",
      kind: "verifier",
    })
  })

  it("存量未分类预填为空", () => {
    expect(draftFromAgent({ ...agent, kinds: [] }).kind).toBe("")
  })

  it("提交入参把单选包成数组并去掉名称首尾空白", () => {
    const input = draftToInput({ ...emptyDraft(), name: " 页面执行 ", kind: "planner" })
    expect(input.kinds).toEqual(["planner"])
    expect(input.name).toBe("页面执行")
  })

  it("未选类型时入参 kinds 为空数组", () => {
    expect(draftToInput({ ...emptyDraft(), name: "x" }).kinds).toEqual([])
  })
})

describe("[P0] 提交前校验", () => {
  const base = { name: "配置", model_config_id: 1, system_prompt: "" }

  it("缺名称时提示名称", () => {
    expect(draftProblem({ ...base, name: "", kinds: ["executor"] })).toBe("请填写名称")
  })

  it("缺模型配置时提示模型配置", () => {
    expect(draftProblem({ ...base, model_config_id: null, kinds: ["executor"] })).toBe(
      "请选择模型配置",
    )
  })

  it("未选类型时提示类型（新建必填）", () => {
    expect(draftProblem({ ...base, kinds: [] })).toBe("请选择类型")
  })

  it("三项齐备时通过", () => {
    expect(draftProblem({ ...base, kinds: ["verifier"] })).toBe("")
  })
})
