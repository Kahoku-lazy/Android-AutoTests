import { mount } from "@vue/test-utils"
import { describe, expect, it } from "vitest"
import BugDetailDrawer from "@/modules/bug-manager/components/BugDetailDrawer.vue"
import type { BugTicket } from "@/modules/bug-manager/types"

function ticket(extra: Partial<BugTicket> = {}): BugTicket {
  return {
    id: 1,
    bug_no: "BUG-0001",
    category: "ui_automation",
    category_label: "UI 自动化",
    title: "步骤未通过：回到桌面",
    status: "open",
    status_label: "待处理",
    task_id: 18,
    task_title: "H6810",
    task_kind: "assistant_sop",
    task_status: "failed",
    agent_id: 0,
    created_by: "",
    created_at: "2026-11-17T10:00:00",
    updated_at: "",
    resolved_at: "",
    detail: "来源任务：#18",
    ...extra,
  }
}

describe("[P0] BUG 单详情四问", () => {
  it("有快照时展示四问，第一项展开，其余折叠", () => {
    const wrapper = mount(BugDetailDrawer, {
      props: {
        modelValue: true,
        loading: false,
        updating: false,
        bug: ticket({
          failure_steps: [
            {
              seq: 1,
              name: "回到桌面",
              expected: "能看见 dock",
              actual: "没看到 dock",
              attempts: 3,
              kind: "verdict",
            },
            {
              seq: 2,
              name: "打开设置",
              expected: "进入设置页",
              actual: "仍在桌面",
              attempts: 1,
              kind: "verdict",
            },
          ],
        }),
      },
    })

    const details = wrapper.findAll("details")
    expect(details).toHaveLength(2)
    expect(details[0].attributes("open")).toBeDefined()
    expect(details[1].attributes("open")).toBeUndefined()
    expect(wrapper.text()).toContain("期望结果")
    expect(wrapper.text()).toContain("能看见 dock")
    expect(wrapper.text()).toContain("步骤未通过")
    expect(wrapper.text()).not.toContain("/tasks/18")
    expect(wrapper.text()).not.toContain("查看报告")
  })

  it("没有快照时退回原文，有报告定位才出现按钮", () => {
    const plain = mount(BugDetailDrawer, {
      props: { modelValue: true, loading: false, updating: false, bug: ticket() },
    })
    expect(plain.text()).toContain("来源任务：#18")
    expect(plain.find("details").exists()).toBe(false)

    const reported = mount(BugDetailDrawer, {
      props: {
        modelValue: true,
        loading: false,
        updating: false,
        bug: ticket({ report_run: "run", report_name: "a.html" }),
      },
    })
    expect(reported.text()).toContain("查看报告")
  })
})
