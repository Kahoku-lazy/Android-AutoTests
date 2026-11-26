import { afterEach, describe, expect, it } from "vitest"
import { mount } from "@vue/test-utils"
import LoginErrorOverlay from "@/views/components/LoginErrorOverlay.vue"

const stubs = {
  "el-dialog": {
    name: "ElDialogStub",

    props: { modelValue: Boolean, title: String, width: String, appendToBody: Boolean },
    emits: ["update:modelValue"],

    template: `
      <div v-if="modelValue" class="el-overlay" @click="close">
        <div
          class="el-dialog"
          :data-append-to-body="appendToBody ? 'true' : 'false'"
          @click.stop
          @keydown.esc="close"
        >
          <header class="el-dialog__header"><span class="el-dialog__title">{{ title }}</span></header>
          <div class="el-dialog__body"><slot /></div>
          <footer class="el-dialog__footer"><slot name="footer" /></footer>
        </div>
      </div>`,
    methods: {
      close() {
        this.$emit("update:modelValue", false)
      },
    },
  },

  "el-button": {
    template: '<button type="button" class="el-button"><slot /></button>',
  },
}

function mountOverlay(props: { visible: boolean; message: string }) {
  return mount(LoginErrorOverlay, {
    props,
    attachTo: document.body,
    global: {
      stubs: { ...stubs, teleport: true, transition: false },
    },
  })
}

describe("[P1] LoginErrorOverlay", () => {
  afterEach(() => {
    document.body.innerHTML = ""
  })

  it("visible=false 时：不渲染内容", () => {
    const wrapper = mountOverlay({ visible: false, message: "失败" })
    expect(wrapper.find(".el-dialog").exists()).toBe(false)
  })

  it("visible=true 时：展示错误文案", () => {
    const wrapper = mountOverlay({ visible: true, message: "密码错误" })
    expect(wrapper.text()).toContain("密码错误")
  })

  it("点「知道了」：触发 close", async () => {
    const wrapper = mountOverlay({ visible: true, message: "失败" })
    await wrapper.find('[data-testid="login-error-dismiss"]').trigger("click")
    expect(wrapper.emitted("close")).toHaveLength(1)
  })

  it("visible=false 时：ESC 不触发 close", () => {
    const wrapper = mountOverlay({ visible: false, message: "失败" })
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }))
    expect(wrapper.emitted("close")).toBeUndefined()
  })

  it("按 ESC：触发 close", async () => {
    const wrapper = mountOverlay({ visible: true, message: "失败" })
    await wrapper.find(".el-dialog").trigger("keydown.esc")
    expect((wrapper.emitted("close") ?? []).length).toBeGreaterThan(0)
  })

  it("点击遮罩：触发 close", async () => {
    const wrapper = mountOverlay({ visible: true, message: "失败" })
    await wrapper.find(".el-overlay").trigger("click")
    expect((wrapper.emitted("close") ?? []).length).toBeGreaterThan(0)
  })

  it("遮罩跳出 transform 包含块：el-dialog 收到 append-to-body", () => {
    const wrapper = mountOverlay({ visible: true, message: "失败" })

    expect(wrapper.find(".el-dialog").attributes("data-append-to-body")).toBe("true")
  })
})
