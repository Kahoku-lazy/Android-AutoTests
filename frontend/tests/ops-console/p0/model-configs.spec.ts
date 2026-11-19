/**
 * [P0] 必测 — 运营模型配置的类型 / 厂商映射与表单联动（spec: ops-model-config）
 *
 * 目录：tests/ops-console/p0/
 * 断言：① 聊天三家、实时语音与语音合成只有 dashscope；② 默认厂商与安全回退；
 * ③ 模型类型列排在模型名称之前；④ 切类型后厂商与密钥变量同步、仍受支持的厂商不被重置；
 * ⑤ 实时语音 / 语音合成只保留一个名称且音色在名称之后；⑥ 语音合成不填地址也能保存。
 */
import { beforeEach, describe, expect, it, vi } from "vitest"
import { flushPromises, mount } from "@vue/test-utils"
import type { DOMWrapper } from "@vue/test-utils"
import {
  defaultProviderForKind,
  keyForProvider,
  modelKindLabel,
  normalizeProvider,
  OPS_MODEL_COLUMNS,
  providersForKind,
} from "@/modules/ops-console/constants"

const api = vi.hoisted(() => ({
  listModelConfigs: vi.fn(),
  createModelConfig: vi.fn(),
  updateModelConfig: vi.fn(),
  deleteModelConfig: vi.fn(),
  discoverModelNames: vi.fn(),
}))

vi.mock("@/modules/ops-console/api", () => api)

import ModelConfigs from "@/modules/ops-console/model-configs.vue"

const ElDrawerStub = {
  props: ["modelValue", "title"],
  template: `<div v-if="modelValue" class="stub-drawer"><slot /></div>`,
}

const ElSelectStub = {
  props: ["modelValue"],
  emits: ["update:modelValue"],
  template: `<select class="stub-select" :value="modelValue" @change="$emit('update:modelValue', $event.target.value)"><slot /></select>`,
}

const ElOptionStub = {
  props: ["value", "label"],
  template: `<option :value="value">{{ label }}</option>`,
}

const ElInputStub = {
  props: ["modelValue", "size"],
  emits: ["update:modelValue"],
  template: `<input class="stub-input" :value="modelValue" @input="$emit('update:modelValue', $event.target.value)" />`,
}

const DoodleBtnStub = {
  emits: ["click"],
  template: `<button class="stub-btn" @click="$emit('click')"><slot /></button>`,
}

const stubs = {
  "el-drawer": ElDrawerStub,
  "el-select": ElSelectStub,
  "el-option": ElOptionStub,
  "el-input": ElInputStub,
  "el-dropdown": { template: `<div class="stub-dropdown"><slot /><slot name="dropdown" /></div>` },
  "el-dropdown-menu": { template: `<div class="stub-dropdown-menu"><slot /></div>` },
  "el-dropdown-item": { template: `<div class="stub-dropdown-item"><slot /></div>` },
  "DoodleBtn": DoodleBtnStub,
  "WorkbenchHeader": { template: `<header class="stub-header" />` },
  "AppTable": { template: `<div class="stub-table" />` },
  "EmptyState": true,
  "ErrorState": true,
  "SkeletonCard": true,
}

function fieldByLabel(wrapper: ReturnType<typeof mount>, label: string): DOMWrapper<Element> {
  const field = wrapper
    .findAll(".sketch-field")
    .find((item) => item.find(".sketch-field__label").text().startsWith(label))
  if (!field) throw new Error(`找不到字段：${label}`)
  return field
}

function optionValues(field: DOMWrapper<Element>) {
  return field.findAll("option").map((item) => (item.element as HTMLOptionElement).value)
}

function selectedValue(field: DOMWrapper<Element>) {
  return (field.find("select").element as HTMLSelectElement).value
}

async function openCreateDrawer() {
  const wrapper = mount(ModelConfigs, { global: { stubs } })
  await flushPromises()
  const createButton = wrapper.findAll("button").find((item) => item.text() === "新建模型")
  if (!createButton) throw new Error("找不到新建模型按钮")
  await createButton.trigger("click")
  return wrapper
}

beforeEach(() => {
  Object.values(api).forEach((fn) => fn.mockReset())
  api.listModelConfigs.mockResolvedValue({
    data: { status: true, data: { configs: [] } },
  })
})

describe("[P0] 模型类型与厂商映射", () => {
  it("聊天支持三家，实时语音与语音合成只支持 dashscope", () => {
    expect(providersForKind("chat").map((item) => item.value)).toEqual([
      "deepseek",
      "dashscope",
      "openai",
    ])
    expect(providersForKind("realtime").map((item) => item.value)).toEqual(["dashscope"])
    expect(providersForKind("tts").map((item) => item.value)).toEqual(["dashscope"])
  })

  it("默认厂商按类型给出，缺省按聊天处理", () => {
    expect(defaultProviderForKind("chat")).toBe("deepseek")
    expect(defaultProviderForKind("realtime")).toBe("dashscope")
    expect(defaultProviderForKind("tts")).toBe("dashscope")
    expect(defaultProviderForKind(undefined)).toBe("deepseek")
  })

  it("归一厂商：受支持保留，不受支持回退默认", () => {
    expect(normalizeProvider("chat", "openai")).toBe("openai")
    expect(normalizeProvider("realtime", "dashscope")).toBe("dashscope")
    expect(normalizeProvider("realtime", "deepseek")).toBe("dashscope")
    expect(normalizeProvider("tts", "openai")).toBe("dashscope")
  })

  it("类型标签覆盖三类，缺失或未知按聊天显示", () => {
    expect(modelKindLabel("chat")).toBe("聊天")
    expect(modelKindLabel("tts")).toBe("语音合成")
    expect(modelKindLabel("realtime")).toBe("实时语音")
    expect(modelKindLabel(undefined)).toBe("聊天")
    expect(modelKindLabel("unknown")).toBe("聊天")
  })

  it("类型列紧随模型首列，首列副行也带类型", () => {
    const props = OPS_MODEL_COLUMNS.map((column) => column.prop)
    expect(props.indexOf("model")).toBe(0)
    expect(props.indexOf("model_kind")).toBe(1)
    expect(props).toContain("actions")
  })

  it("密钥变量与厂商成对", () => {
    expect(keyForProvider("deepseek")).toBe("DEEPSEEK_API_KEY")
    expect(keyForProvider("dashscope")).toBe("DASHSCOPE_API_KEY")
    expect(keyForProvider("openai")).toBe("OPENAI_API_KEY")
    expect(keyForProvider("unknown")).toBe("")
  })
})

describe("[P0] 新建模型抽屉的厂商联动", () => {
  it("默认组合为聊天 + deepseek，厂商下拉列出三家", async () => {
    const wrapper = await openCreateDrawer()

    const kindField = fieldByLabel(wrapper, "模型类型")
    expect(selectedValue(kindField)).toBe("chat")

    const providerField = fieldByLabel(wrapper, "厂商")
    expect(selectedValue(providerField)).toBe("deepseek")
    expect(optionValues(providerField)).toEqual(["deepseek", "dashscope", "openai"])

    const keyInput = fieldByLabel(wrapper, "密钥环境变量").find("input")
    expect((keyInput.element as HTMLInputElement).value).toBe("DEEPSEEK_API_KEY")
  })

  it("切到实时语音后厂商只剩 dashscope，密钥变量同步", async () => {
    const wrapper = await openCreateDrawer()
    const kindField = fieldByLabel(wrapper, "模型类型")

    await kindField.find("select").setValue("realtime")

    const providerField = fieldByLabel(wrapper, "厂商")
    expect(optionValues(providerField)).toEqual(["dashscope"])
    expect(selectedValue(providerField)).toBe("dashscope")
    const keyInput = fieldByLabel(wrapper, "密钥环境变量").find("input")
    expect((keyInput.element as HTMLInputElement).value).toBe("DASHSCOPE_API_KEY")
  })

  it("切到语音合成 / 切回聊天时，仍受支持的 dashscope 不被重置", async () => {
    const wrapper = await openCreateDrawer()
    const kindField = fieldByLabel(wrapper, "模型类型")

    await kindField.find("select").setValue("realtime")
    await kindField.find("select").setValue("tts")
    expect(selectedValue(fieldByLabel(wrapper, "厂商"))).toBe("dashscope")
    expect(optionValues(fieldByLabel(wrapper, "厂商"))).toEqual(["dashscope"])

    await kindField.find("select").setValue("chat")
    expect(selectedValue(fieldByLabel(wrapper, "厂商"))).toBe("dashscope")
    expect(optionValues(fieldByLabel(wrapper, "厂商"))).toEqual(["deepseek", "dashscope", "openai"])
  })
})

describe("[P0] 实时语音 / 语音合成的单模型与音色位置", () => {
  it("两类语音只有一个名称输入，且没有添加 / 删除", async () => {
    const wrapper = await openCreateDrawer()
    const kindField = fieldByLabel(wrapper, "模型类型")

    for (const kind of ["realtime", "tts"]) {
      await kindField.find("select").setValue(kind)
      const nameField = fieldByLabel(wrapper, "模型名称")
      expect(nameField.findAll("input")).toHaveLength(1)
      expect(nameField.text()).not.toContain("+ 添加一行")
      expect(nameField.text()).not.toContain("删除")
    }
  })

  it("聊天多行切到实时语音只留第一行，切回聊天可继续添加", async () => {
    const wrapper = await openCreateDrawer()
    const addButton = () => wrapper.findAll("button").find((item) => item.text() === "+ 添加一行")

    await addButton()?.trigger("click")
    await addButton()?.trigger("click")
    const inputs = fieldByLabel(wrapper, "模型名称").findAll("input")
    expect(inputs).toHaveLength(3)
    await inputs[0].setValue("model-a")
    await inputs[1].setValue("model-b")
    await inputs[2].setValue("model-c")

    await fieldByLabel(wrapper, "模型类型").find("select").setValue("realtime")
    const single = fieldByLabel(wrapper, "模型名称").findAll("input")
    expect(single).toHaveLength(1)
    expect((single[0].element as HTMLInputElement).value).toBe("model-a")

    await fieldByLabel(wrapper, "模型类型").find("select").setValue("chat")
    expect(fieldByLabel(wrapper, "模型名称").findAll("input")).toHaveLength(1)
    expect(addButton()).toBeTruthy()
  })

  it("音色紧跟在模型名称之后", async () => {
    const wrapper = await openCreateDrawer()
    await fieldByLabel(wrapper, "模型类型").find("select").setValue("tts")

    const labels = wrapper
      .findAll(".sketch-field__label")
      .map((item) => item.text().replace(/\s+/g, ""))
    expect(labels.indexOf("音色")).toBe(labels.indexOf("模型名称") + 1)
  })

  it("语音合成只提交一个名称，且不要求 API 地址", async () => {
    api.createModelConfig.mockResolvedValue({ data: { status: true, data: {} } })
    const wrapper = await openCreateDrawer()

    await fieldByLabel(wrapper, "模型类型").find("select").setValue("tts")
    await fieldByLabel(wrapper, "模型名称").find("input").setValue("qwen3-tts-flash")
    await fieldByLabel(wrapper, "音色").find("select").setValue("Cherry")

    const saveButton = wrapper.findAll("button").find((item) => item.text() === "保存")
    await saveButton?.trigger("click")
    await flushPromises()

    expect(api.createModelConfig).toHaveBeenCalledTimes(1)
    const payload = api.createModelConfig.mock.calls[0][0]
    expect(payload.model_kind).toBe("tts")
    expect(payload.model_name).toBe("qwen3-tts-flash")
    expect(payload.voice).toBe("Cherry")
    expect(payload.base_url).toBe("")
  })
})
