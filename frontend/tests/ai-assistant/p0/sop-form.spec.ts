import { describe, expect, it } from "vitest"
import {
  sameCardAllowed,
  sopCreateError,
  sopRunError,
  sopRunFields,
} from "@/modules/ai-assistant/helpers/sop-form"

describe("SOP 表单", () => {
  it("两侧都必选", () => {
    expect(
      sopCreateError({
        name: "检查",
        orchestration: "sop",
        executorId: "",
        verifierId: "20261117_B",
        leaderId: "",
        members: [],
      }),
    ).toBe("先选执行助手")
    expect(
      sopCreateError({
        name: "检查",
        orchestration: "sop",
        executorId: "20261117_A",
        verifierId: "",
        leaderId: "",
        members: [],
      }),
    ).toBe("先选验收助手")
  })

  it("同一张名片可以同时担任两侧", () => {
    const input = {
      name: "自检",
      orchestration: "sop" as const,
      executorId: "20261117_A",
      verifierId: "20261117_A",
      leaderId: "",
      members: [],
    }
    expect(sopCreateError(input)).toBe("")
    expect(sameCardAllowed(input.executorId, input.verifierId)).toBe(true)
  })

  it("设备必选，请求字段不含提示词和工具清单", () => {
    const missing = {
      workflowId: 7,
      source: "yaml" as const,
      yamlName: "steps.yaml",
      caseCount: 0,
      serial: "",
    }
    expect(sopRunError(missing)).toBe("先选择设备")
    const input = {
      workflowId: 7,
      source: "yaml" as const,
      yamlName: "steps.yaml",
      caseCount: 0,
      serial: "RF8N21MSW7A",
    }
    expect(sopRunError(input)).toBe("")
    expect(sopRunFields(input)).toEqual(["workflow_id", "config", "device_serial"])
    expect(sopRunFields(input).join(",")).not.toContain("prompt")
    expect(sopRunFields(input).join(",")).not.toContain("tools")
  })
})
