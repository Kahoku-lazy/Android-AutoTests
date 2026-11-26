import { flushPromises, mount } from "@vue/test-utils"
import { defineComponent } from "vue"
import { beforeEach, describe, expect, it, vi } from "vitest"
import { ref } from "vue"
import OpsUsers from "@/modules/ops-console/index.vue"
import { disableOpsUsers, listOpsUsers, purgeOpsUsers } from "@/modules/ops-console/api"
import type { OpsUser } from "@/modules/ops-console/types"

const isSuperuser = ref(false)

vi.mock("@/shared/composables/useAuthUser", () => ({
  useAuthUser: () => ({ isSuperuser, isOperator: ref(true) }),
}))

vi.mock("@/modules/ops-console/api", () => ({
  listOpsUsers: vi.fn(),
  disableOpsUsers: vi.fn(),
  purgeOpsUsers: vi.fn(),
  setOpsUserActive: vi.fn(),
  setOpsUserOperator: vi.fn(),
  resetOpsUserPassword: vi.fn(),
}))

vi.mock("element-plus", () => ({
  ElMessage: { success: vi.fn(), error: vi.fn() },
  ElMessageBox: {
    confirm: vi.fn().mockResolvedValue("confirm"),
    prompt: vi.fn().mockRejectedValue("cancel"),
  },
}))

const TableStub = defineComponent({
  props: { dataSource: { type: Array, default: () => [] } },
  setup(props, { slots }) {
    return () => [
      slots["header-_select"]?.(),
      ...(props.dataSource as { id: number }[]).map((record) =>
        slots["cell-_select"]?.({ record }),
      ),
    ]
  },
})

const mockedList = vi.mocked(listOpsUsers)
const mockedDisable = vi.mocked(disableOpsUsers)
const mockedPurge = vi.mocked(purgeOpsUsers)

function row(id: number, identity: OpsUser["identity"]): OpsUser {
  return {
    id,
    username: `u${id}`,
    email: "",
    identity,
    is_active: true,
    date_joined: "",
    last_login: "",
  }
}

beforeEach(() => {
  isSuperuser.value = false
  mockedList.mockReset()
  mockedDisable.mockReset()
  mockedPurge.mockReset()
  mockedList.mockResolvedValue({
    data: {
      status: true,
      data: {
        users: [row(1, "user"), row(2, "superuser"), row(3, "operator")],
        total: 3,
        page: 1,
        page_size: 10,
      },
    },
  })
})

describe("[P0] 用户管理批量动作", () => {
  it("超管行与运营行的复选框禁用，普通用户行可选", async () => {
    const wrapper = mount(OpsUsers, {
      global: { stubs: { "OpsUserDrawer": true, "AppTable": TableStub, "el-input": true } },
    })
    await flushPromises()
    const boxes = wrapper.findAll('[data-testid="ops-row-check"]')
    expect((boxes[0].element as HTMLInputElement).disabled).toBe(false)
    expect((boxes[1].element as HTMLInputElement).disabled).toBe(true)
    expect((boxes[2].element as HTMLInputElement).disabled).toBe(true)
  })

  it("表头全选只勾当前页可管理的行", async () => {
    const wrapper = mount(OpsUsers, {
      global: { stubs: { "OpsUserDrawer": true, "AppTable": TableStub, "el-input": true } },
    })
    await flushPromises()
    await wrapper.find('[data-testid="ops-page-check"]').setValue(true)
    const boxes = wrapper.findAll('[data-testid="ops-row-check"]')
    expect((boxes[0].element as HTMLInputElement).checked).toBe(true)
    expect((boxes[1].element as HTMLInputElement).checked).toBe(false)
  })

  it("运营界面没有批量注销按钮", async () => {
    const wrapper = mount(OpsUsers, {
      global: { stubs: { "OpsUserDrawer": true, "AppTable": TableStub, "el-input": true } },
    })
    await flushPromises()
    expect(wrapper.find('[data-testid="ops-batch-purge"]').exists()).toBe(false)
  })

  it("超管能看到批量注销；确认被取消时不发请求", async () => {
    isSuperuser.value = true
    const wrapper = mount(OpsUsers, {
      global: { stubs: { "OpsUserDrawer": true, "AppTable": TableStub, "el-input": true } },
    })
    await flushPromises()
    const box = wrapper.find('[data-testid="ops-row-check"]')
    await box.setValue(true)
    await wrapper.find('[data-testid="ops-batch-purge"]').trigger("click")
    await flushPromises()
    expect(mockedPurge).not.toHaveBeenCalled()
  })

  it("批量停用成功后重新请求列表", async () => {
    const wrapper = mount(OpsUsers, {
      global: { stubs: { "OpsUserDrawer": true, "AppTable": TableStub, "el-input": true } },
    })
    await flushPromises()
    await wrapper.find('[data-testid="ops-row-check"]').setValue(true)
    mockedDisable.mockResolvedValue({
      data: {
        status: true,
        data: {
          results: [{ user_id: 1, outcome: "disabled", reason: "" }],
          counts: { disabled: 1, skipped: 0, rejected: 0 },
        },
      },
    })
    await wrapper.find('[data-testid="ops-batch-disable"]').trigger("click")
    await flushPromises()
    expect(mockedDisable).toHaveBeenCalledWith([1])
    expect(mockedList.mock.calls.length).toBeGreaterThan(1)
  })
})
