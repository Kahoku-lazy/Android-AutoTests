/**
 * [P0] 必测 — 「保存到元素定位」弹窗的目录来源与两条提交分支
 * 目录：tests/device-inspector/p0/
 *
 * 口径来源：openspec/specs/inspector-save-to-elements 与 device-inspector-page。
 * 项目化迁移后目录在 \`el_locator_directories\` 里，弹窗只能从元素定位项目树取目录；
 * 单测环境不注册 el-* 按需组件，故按本仓既有做法用替身驱动，断言弹窗下发的真实契约。
 */
import { defineComponent, h, inject, provide, type PropType } from 'vue'
import { createPinia, setActivePinia } from 'pinia'
import { mount, flushPromises } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('element-plus', () => ({
  ElMessage: { success: vi.fn(), warning: vi.fn(), error: vi.fn() },
}))
vi.mock('@/shared/api-client', () => ({
  formatApiError: (_error: unknown, fallback: string) => fallback,
  default: {},
}))
vi.mock('@/modules/element-locator/api', () => ({
  getLocatorProjectTree: vi.fn(),
}))

import { getLocatorProjectTree } from '@/modules/element-locator/api'
import SaveToElementsDialog from '@/modules/device-inspector/components/SaveToElementsDialog.vue'
import { useElementStore } from '@/modules/device-inspector/store'

/** 项目树：目录两级（测试目录 / govee），页面分别挂在根、一级目录、二级目录下 */
const PROJECT_TREE = [
  {
    type: 'directory',
    id: 5,
    name: '测试目录',
    children: [
      {
        type: 'directory',
        id: 6,
        name: 'govee',
        children: [{ type: 'file', kind: 'page', id: 50, name: '设备首页' }],
      },
      { type: 'file', kind: 'page', id: 49, name: '目录下页面' },
    ],
  },
  { type: 'file', kind: 'page', id: 40, name: '根下页面' },
]

// ── 替身：把 v-model 与选项显式化，便于断言弹窗下发的契约 ──
const selectCtx = Symbol('select')
const radioCtx = Symbol('radio')
/** 表单校验结果可切换：默认通过，用于覆盖「校验不通过不提交」 */
let formValidateImpl: () => Promise<void> = () => Promise.resolve()

function flattenDirs(options: any[], prefix: string[] = []): { path: string[]; label: string }[] {
  const out: { path: string[]; label: string }[] = []
  for (const option of options || []) {
    const path = [...prefix, option.label]
    out.push({ path, label: path.join(' / ') })
    out.push(...flattenDirs(option.children, path))
  }
  return out
}

const ElDialogStub = defineComponent({
  props: { modelValue: Boolean, title: String },
  setup(_props, { slots }) {
    return () => h('div', { class: 'stub-dialog' }, [slots.default?.(), slots.footer?.()])
  },
})
const ElFormStub = defineComponent({
  props: { model: Object, rules: Object },
  setup(_props, { slots, expose }) {
    expose({ validate: () => formValidateImpl() })
    return () => h('div', { class: 'stub-form' }, slots.default?.())
  },
})
const ElFormItemStub = defineComponent({
  setup(_props, { slots }) {
    return () => h('div', { class: 'stub-form-item' }, slots.default?.())
  },
})
const ElCascaderStub = defineComponent({
  props: { modelValue: { type: Array as PropType<string[]>, default: () => [] }, options: { type: Array, default: () => [] } },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    return () =>
      h(
        'div',
        { class: 'stub-cascader' },
        flattenDirs(props.options as any[]).map(({ path, label }) =>
          h(
            'button',
            { class: 'stub-dir', 'data-path': label, onClick: () => emit('update:modelValue', path) },
            label,
          ),
        ),
      )
  },
})
const ElRadioGroupStub = defineComponent({
  props: { modelValue: String },
  emits: ['update:modelValue'],
  setup(_props, { slots, emit }) {
    provide(radioCtx, (value: string) => emit('update:modelValue', value))
    return () => h('div', { class: 'stub-radio-group' }, slots.default?.())
  },
})
const ElRadioButtonStub = defineComponent({
  props: { value: String },
  setup(props, { slots }) {
    const pick = inject<(value: string) => void>(radioCtx, () => {})
    return () => h('button', { class: 'stub-radio', 'data-value': props.value, onClick: () => pick(props.value!) }, slots.default?.())
  },
})
const ElSelectStub = defineComponent({
  props: { modelValue: [Number, String, null] },
  emits: ['update:modelValue'],
  setup(_props, { slots, emit }) {
    provide(selectCtx, (value: unknown) => emit('update:modelValue', value))
    return () => h('div', { class: 'stub-select' }, slots.default?.())
  },
})
const ElOptionStub = defineComponent({
  props: { value: [Number, String], label: String },
  setup(props, { slots }) {
    const pick = inject<(value: unknown) => void>(selectCtx, () => {})
    return () =>
      h('button', { class: 'stub-option', 'data-value': String(props.value), onClick: () => pick(props.value) }, props.label ?? slots.default?.())
  },
})
const ElInputStub = defineComponent({
  props: { modelValue: String },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    return () =>
      h('input', {
        class: 'stub-input',
        value: props.modelValue,
        onInput: (event: Event) => emit('update:modelValue', (event.target as HTMLInputElement).value),
      })
  },
})
const ElButtonStub = defineComponent({
  props: { loading: Boolean, type: String },
  setup(_props, { slots, emit }) {
    return () => h('button', { class: 'stub-button', onClick: () => emit('click') }, slots.default?.())
  },
})

const STUBS = {
  'el-dialog': ElDialogStub,
  'el-form': ElFormStub,
  'el-form-item': ElFormItemStub,
  'el-cascader': ElCascaderStub,
  'el-radio-group': ElRadioGroupStub,
  'el-radio-button': ElRadioButtonStub,
  'el-select': ElSelectStub,
  'el-option': ElOptionStub,
  'el-input': ElInputStub,
  'el-button': ElButtonStub,
}

async function mountDialog() {
  // 组件与用例必须共用同一个 pinia 实例，否则用例改的是另一个 store
  const pinia = createPinia()
  setActivePinia(pinia)
  const store = useElementStore()
  store.snapshot = { snapshot_id: 9, package: 'com.govee.home' }
  store.saveToElements = vi.fn()
  const wrapper = mount(SaveToElementsDialog, {
    global: {
      plugins: [pinia],
      stubs: STUBS,
      directives: { loading: () => {} },
    },
  })
  // 弹窗打开时才拉目录树（watch on store.saveDialogVisible）
  store.saveDialogVisible = true
  await flushPromises()
  return { wrapper, store }
}

beforeEach(() => {
  setActivePinia(createPinia())
  formValidateImpl = () => Promise.resolve()
  vi.mocked(getLocatorProjectTree).mockResolvedValue({
    data: { status: true, data: { tree: PROJECT_TREE } },
  } as never)
})

describe('[P0] SaveToElementsDialog 目录来源', () => {
  it('级联选项只含目录节点：目录名逐层嵌套，页面不进级联', async () => {
    const { wrapper } = await mountDialog()
    const paths = wrapper.findAll('.stub-dir').map((node) => node.attributes('data-path'))
    expect(paths).toEqual(['测试目录', '测试目录 / govee'])
    expect(paths.join(' ')).not.toContain('页面')
  })

  it('未选目录时页面列表取项目根下的页面', async () => {
    const { wrapper } = await mountDialog()
    expect(wrapper.findAll('.stub-option').map((n) => n.text())).toEqual(['根下页面'])
  })

  it('选中一级目录后页面列表换成该目录下的页面', async () => {
    const { wrapper } = await mountDialog()
    await wrapper.find('.stub-dir[data-path="测试目录"]').trigger('click')
    expect(wrapper.findAll('.stub-option').map((n) => n.text())).toEqual(['目录下页面'])
  })

  it('选中二级目录后页面列表换成该目录下的页面', async () => {
    const { wrapper } = await mountDialog()
    await wrapper.find('.stub-dir[data-path="测试目录 / govee"]').trigger('click')
    expect(wrapper.findAll('.stub-option').map((n) => n.text())).toEqual(['设备首页'])
  })
})

describe('[P0] SaveToElementsDialog 提交分支', () => {
  it('已有页面：提交 page_id，不带 folder_path / page_label', async () => {
    const { wrapper, store } = await mountDialog()
    await wrapper.find('.stub-dir[data-path="测试目录 / govee"]').trigger('click')
    await wrapper.find('.stub-option[data-value="50"]').trigger('click')
    await wrapper.find('[data-testid="save-confirm-btn"]').trigger('click')
    await flushPromises()

    expect(store.saveToElements).toHaveBeenCalledWith({ pageId: 50, pageLabel: '', folderPath: '' })
  })

  it('新建页面：提交 page_label + folder_path，默认名取快照包名', async () => {
    const { wrapper, store } = await mountDialog()
    await wrapper.find('.stub-radio[data-value="create"]').trigger('click')
    await wrapper.find('.stub-dir[data-path="测试目录 / govee"]').trigger('click')
    expect((wrapper.find('.stub-input').element as HTMLInputElement).value).toBe('com.govee.home')

    await wrapper.find('[data-testid="save-confirm-btn"]').trigger('click')
    await flushPromises()

    expect(store.saveToElements).toHaveBeenCalledWith({
      pageLabel: 'com.govee.home',
      folderPath: '测试目录 / govee',
    })
  })

  it('必填规则登记在表单上（未选页面 / 未填页面名都要拦）', async () => {
    const { wrapper } = await mountDialog()
    const rules = wrapper.findComponent(ElFormStub).props('rules') as Record<string, unknown[]>
    expect(Object.keys(rules).sort()).toEqual(['newPageLabel', 'selectedPageId'])
    expect(rules.selectedPageId[0]).toMatchObject({ required: true })
    expect(rules.newPageLabel[0]).toMatchObject({ required: true })
  })

  it('校验不通过时不提交（validate reject 直接返回）', async () => {
    const { wrapper, store } = await mountDialog()
    formValidateImpl = () => Promise.reject(new Error('invalid'))
    await wrapper.find('[data-testid="save-confirm-btn"]').trigger('click')
    await flushPromises()

    expect(store.saveToElements).not.toHaveBeenCalled()
  })
})
