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
    detail: "",
    ...extra,
  }
}

function mountWith(detail: string) {
  return mount(BugDetailDrawer, {
    props: { modelValue: true, loading: false, updating: false, bug: ticket({ detail }) },
  })
}

describe("[P0] BUG 详情错误内容逐行渲染", () => {
  it("按行拆分，行首标签落在加粗单元里", () => {
    const wrapper = mountWith("来源任务：#18\n失败原因：点击未命中")
    const lines = wrapper.findAll(".bug-detail__line")
    expect(lines).toHaveLength(2)
    const keys = wrapper.findAll(".bug-detail__line-key")
    expect(keys).toHaveLength(2)
    expect(keys[0].text()).toBe("来源任务：")
    expect(keys[1].text()).toBe("失败原因：")
    expect(lines[0].text()).toBe("来源任务：#18")
  })

  it("没有行首标签的行整行当正文，不产生加粗单元", () => {
    const wrapper = mountWith("java.lang.NullPointerException")
    const lines = wrapper.findAll(".bug-detail__line")
    expect(lines).toHaveLength(1)
    expect(wrapper.findAll(".bug-detail__line-key")).toHaveLength(0)
    expect(lines[0].text()).toBe("java.lang.NullPointerException")
  })

  it("缩进行保留前导空白", () => {
    const wrapper = mountWith("  at com.example.Foo.bar(Foo.java:42)")
    const line = wrapper.find(".bug-detail__line")
    expect(line.element.textContent?.startsWith("  ")).toBe(true)
  })

  it("正文为空时只显示占位符", () => {
    const wrapper = mountWith("")
    const lines = wrapper.findAll(".bug-detail__line")
    expect(lines).toHaveLength(1)
    expect(lines[0].text()).toBe("—")
    expect(wrapper.find("pre").exists()).toBe(false)
  })
})
