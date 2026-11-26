import { mount } from "@vue/test-utils"
import { describe, expect, it } from "vitest"
import { defineComponent, ref } from "vue"
import { hasUnsavedChanges, useUnsavedChanges } from "@/shared/composables/useUnsavedChanges"

function mountProbe(dirty: ReturnType<typeof ref<boolean>>) {
  const Probe = defineComponent({
    setup() {
      useUnsavedChanges(() => dirty.value)
      return () => null
    },
  })
  return mount(Probe)
}

describe("[P0] 全局未保存登记", () => {
  it("有页面脏时登记，干净后撤销", async () => {
    const dirty = ref(true)
    const wrapper = mountProbe(dirty)
    expect(hasUnsavedChanges()).toBe(true)

    dirty.value = false
    await wrapper.vm.$nextTick()
    expect(hasUnsavedChanges()).toBe(false)
    wrapper.unmount()
  })

  it("页面卸载后自动撤销登记", () => {
    const wrapper = mountProbe(ref(true))
    expect(hasUnsavedChanges()).toBe(true)
    wrapper.unmount()
    expect(hasUnsavedChanges()).toBe(false)
  })

  it("多个页面互不覆盖：一个卸载不影响另一个脏页面", () => {
    const first = mountProbe(ref(true))
    const second = mountProbe(ref(true))
    expect(hasUnsavedChanges()).toBe(true)

    first.unmount()
    expect(hasUnsavedChanges()).toBe(true)

    second.unmount()
    expect(hasUnsavedChanges()).toBe(false)
  })
})
