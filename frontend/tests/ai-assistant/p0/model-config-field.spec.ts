/**
 * [P0] 模型配置区块：API Key 不得被浏览器当成登录密码框（凭据提示/填充）
 *
 * 背景：该区块是真正的 `<form>`，内部「模型名文本输入 + API Key 密码框」的组合会被
 * 浏览器密码管理器判定为登录表单；`autocomplete="new-password"` 是阻止该判定的标准做法。
 */
import { describe, expect, it } from "vitest"
import { mount } from "@vue/test-utils"
import ModelConfigField from "@/modules/ai-assistant/components/ModelConfigField.vue"

const stubs = {
  "el-form": { template: "<form><slot /></form>" },
  "el-form-item": { props: ["label"], template: '<div class="el-form-item"><slot /></div>' },
  "el-select": {
    props: ["modelValue"],
    emits: ["update:modelValue"],
    template: '<select class="el-select"><slot /></select>',
  },
  "el-option": { props: ["label", "value"], template: "<option />" },
  "el-input": {
    props: ["modelValue", "autocomplete", "type"],
    emits: ["update:modelValue"],
    template:
      '<input class="el-input" :type="type" :value="modelValue" :autocomplete="autocomplete" @input="$emit(\'update:modelValue\', $event.target.value)" />',
  },
}

function mountField(props: Record<string, unknown> = {}) {
  return mount(ModelConfigField, {
    props: {
      label: "执行模型 Executor",
      modelValue: { provider: "deepseek", model_name: "deepseek-v4-pro" },
      ...props,
    },
    global: { stubs },
  })
}

describe("模型配置区块", () => {
  it("API Key 标 new-password —— 浏览器不再把配置表单当登录表单", () => {
    const w = mountField()
    const password = w.find('input[type="password"]')
    expect(password.exists()).toBe(true)
    expect(password.attributes("autocomplete")).toBe("new-password")
  })

  it("需要图片的角色选中已知纯文本模型时，提示升级为告警样式", () => {
    const textOnly = mountField({ needsImage: true })
    expect(textOnly.find(".model-hint").classes()).toContain("model-hint--warn")

    const multimodal = mountField({
      needsImage: true,
      modelValue: { provider: "deepseek", model_name: "deepseek-flash" },
    })
    expect(multimodal.find(".model-hint").classes()).not.toContain("model-hint--warn")

    const planner = mountField({ needsImage: false })
    expect(planner.find(".model-hint").exists()).toBe(false)
  })
})
