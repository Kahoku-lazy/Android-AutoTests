/**
 * [P0] 单模型调试台：接口契约（无固定超时 + serial）、设备候选与授权确认、
 * 对话编排、工具调用轨迹、调试页三层结构与归属标注
 */
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, type VueWrapper } from '@vue/test-utils'
import { ref, nextTick } from 'vue'

const { confirmMock } = vi.hoisted(() => ({ confirmMock: vi.fn() }))
vi.mock('element-plus', () => ({
  ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
  ElMessageBox: { confirm: confirmMock },
}))

const { routerPush } = vi.hoisted(() => ({ routerPush: vi.fn() }))
vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { role: 'executor' } }),
  useRouter: () => ({ push: routerPush }),
}))

const post = vi.fn()
const get = vi.fn()

// 只替换 HTTP 出口，保留真实 formatApiError
vi.mock('@/shared/api-client', async () => {
  const errors = await import('@/shared/types/api-error')
  return {
    default: {
      post: (...args: unknown[]) => post(...args),
      get: (...args: unknown[]) => get(...args),
    },
    formatApiError: errors.formatApiError,
  }
})

const fetchConfig = vi.fn()
const chat = vi.fn()

vi.mock('@/modules/ai-assistant/api/toolbox', () => ({
  fetchModelDebugConfig: (...args: unknown[]) => fetchConfig(...args),
  chatWithModelDebug: (...args: unknown[]) => chat(...args),
}))

import {
  KNOWLEDGE_RAG_NOTE,
  MODEL_DEBUG_ANSWER_ERROR_LABEL,
  MODEL_DEBUG_ANSWER_LABEL,
  MODEL_DEBUG_SCOPE_NOTE,
  MODEL_DEBUG_THINKING_LABEL,
  MODEL_DEBUG_TRACE_LABEL,
  SKILL_SHARED_NOTE,
} from '@/modules/ai-assistant/constants'
import { useModelDebug } from '@/modules/ai-assistant/composables/useModelDebug'
import ModelDebugPage from '@/modules/ai-assistant/ModelDebugPage.vue'

/** 设备候选夹具：只有第一台是「在线 + 未被占用」 */
const DEVICES = [
  { serial: 'ONLINE-1', model: 'SM-S9010', status: 'ONLINE', occupied_by: '' },
  { serial: 'BUSY-1', model: 'SM-BUSY', status: 'ONLINE', occupied_by: 'task-9' },
  { serial: 'OFF-1', model: 'SM-OFF', status: 'OFFLINE', occupied_by: '' },
]

/** 设备列表走同一个 HTTP 出口：默认返回上面的夹具 */
function mockDeviceList(): void {
  get.mockResolvedValue({ data: { status: true, data: { devices: DEVICES } } })
}

const CONFIG = {
  status: true,
  data: {
    agent_id: 10,
    agent_name: '自动化小助手',
    role: {
      role: 'executor',
      label: '执行模型 Executor',
      vision: true,
      needs_device: true,
      model: {
        provider: 'deepseek',
        model_name: 'deepseek-chat',
        has_api_key: true,
        configured: true,
      },
      prompt: 'EXECUTOR-PROMPT',
      tools: [
        { name: 'tap_screen', read_only: false, category: '设备控制', enabled: true },
        { name: 'input_text', read_only: false, category: '设备控制', enabled: true },
        { name: 'screenshot_page', read_only: true, category: '设备检查器', enabled: false },
      ],
    },
    skills: { gate_on: true, shared_by_roles: true, items: [{ name: 'skill-a', path: '/p/a' }] },
    knowledge: {
      gate_on: false,
      enabled_source_ids: [],
      file_count: 1,
      files: [{ id: 'doc/a.md', name: 'a.md', type: 'root' }],
      wired_to_runtime: false,
    },
  },
}

describe('模型调试接口契约', () => {
  beforeEach(() => {
    post.mockReset()
    get.mockReset()
  })

  it('对话走 /ai/model-debug/{role}/chat/，带 serial 且不设超时', async () => {
    const real =
      await vi.importActual<typeof import('@/modules/ai-assistant/api/toolbox')>(
        '@/modules/ai-assistant/api/toolbox',
      )
    post.mockResolvedValueOnce({ data: { status: true, data: { reply: 'ok' } } })

    await real.chatWithModelDebug('executor', '你好', 'ONLINE-1')

    // 只有两个实参：不传 timeout 配置 = 前端不设等待上限
    expect(post).toHaveBeenCalledWith('/ai/model-debug/executor/chat/', {
      text: '你好',
      serial: 'ONLINE-1',
    })
    expect(post.mock.calls[0]).toHaveLength(2)

    get.mockResolvedValueOnce({ data: { status: true, data: {} } })
    await real.fetchModelDebugConfig('planner')
    expect(get).toHaveBeenCalledWith('/ai/model-debug/planner/')
  })
})

describe('useModelDebug', () => {
  beforeEach(() => {
    fetchConfig.mockReset()
    chat.mockReset()
    get.mockReset()
    mockDeviceList()
  })

  it('加载配置并按角色请求', async () => {
    fetchConfig.mockResolvedValue(CONFIG)
    const { config } = useModelDebug(ref('executor'))

    await vi.waitFor(() => expect(config.value?.role.role).toBe('executor'))
    expect(fetchConfig).toHaveBeenCalledWith('executor')
  })

  it('发送后追加用户与助手两条消息', async () => {
    fetchConfig.mockResolvedValue(CONFIG)
    chat.mockResolvedValue({
      status: true,
      data: { role: 'executor', label: '执行模型', model_name: 'deepseek-chat', reply: 'REPLY' },
    })
    const { config, messages, question, sending, serial, send } = useModelDebug(ref('executor'))
    await vi.waitFor(() => expect(config.value).toBeTruthy())

    serial.value = 'ONLINE-1'
    question.value = '你好'
    await send()

    expect(chat).toHaveBeenCalledWith('executor', '你好', 'ONLINE-1')
    expect(messages.value.map((item) => item.role)).toEqual(['user', 'assistant'])
    expect(messages.value[1].content).toBe('REPLY')
    expect(messages.value[1].model_name).toBe('deepseek-chat')
    expect(sending.value).toBe(false)
    expect(question.value).toBe('')
  })

  it('设备候选只保留在线且未被占用的设备', async () => {
    fetchConfig.mockResolvedValue(CONFIG)
    const { devices } = useModelDebug(ref('executor'))

    await vi.waitFor(() => expect(devices.value).toHaveLength(1))
    expect(devices.value[0].serial).toBe('ONLINE-1')
  })

  it('需要设备的角色：未选设备不能发且 send 不发请求', async () => {
    fetchConfig.mockResolvedValue(CONFIG)
    const { config, question, serial, canSend, send } = useModelDebug(ref('executor'))
    await vi.waitFor(() => expect(config.value).toBeTruthy())

    question.value = '跑一下'
    expect(canSend.value).toBe(false)

    await send()
    expect(chat).not.toHaveBeenCalled()

    serial.value = 'ONLINE-1'
    expect(canSend.value).toBe(true)
  })

  it('助手消息带出本轮工具调用轨迹', async () => {
    fetchConfig.mockResolvedValue(CONFIG)
    chat.mockResolvedValue({
      status: true,
      data: {
        role: 'executor',
        label: '执行模型',
        model_name: 'deepseek-chat',
        reply: 'REPLY',
        tool_usage: [{ type: 'call', name: 'tap_screen', input: { serial: 'ONLINE-1' } }],
      },
    })
    const { config, messages, question, serial, send } = useModelDebug(ref('executor'))
    await vi.waitFor(() => expect(config.value).toBeTruthy())

    serial.value = 'ONLINE-1'
    question.value = '点一下'
    await send()

    expect(messages.value[1].tool_usage).toHaveLength(1)
    expect(messages.value[1].tool_usage?.[0].name).toBe('tap_screen')
  })

  it('调用失败时追加可读错误且不改动输入', async () => {
    fetchConfig.mockResolvedValue(CONFIG)
    chat.mockRejectedValue({
      response: { status: 400, data: { status: false, message: '「执行模型 Executor」的 api_key 未配置' } },
    })
    const { config, messages, question, serial, send } = useModelDebug(ref('executor'))
    await vi.waitFor(() => expect(config.value).toBeTruthy())

    serial.value = 'ONLINE-1'
    question.value = '你好'
    await send()

    expect(messages.value).toHaveLength(2)
    expect(messages.value[1].content).toContain('api_key 未配置')
    expect(messages.value[1].error).toBe(true)
  })

  it('空输入不发请求', async () => {
    fetchConfig.mockResolvedValue(CONFIG)
    const { config, question, send } = useModelDebug(ref('executor'))
    await vi.waitFor(() => expect(config.value).toBeTruthy())

    question.value = '   '
    await send()

    expect(chat).not.toHaveBeenCalled()
  })
})

describe('ModelDebugPage', () => {
  beforeEach(() => {
    fetchConfig.mockReset().mockResolvedValue(CONFIG)
    chat.mockReset()
    routerPush.mockReset()
    confirmMock.mockReset()
    get.mockReset()
    mockDeviceList()
  })

  function mountPage() {
    return mount(ModelDebugPage, {
      global: {
        stubs: {
          WorkbenchHeader: true,
          WorkbenchCrumbs: true,
          // 设备下拉用原生 select 承载 v-model，便于断言选用设备后的行为
          'el-select': {
            props: ['modelValue'],
            emits: ['update:modelValue'],
            template:
              '<select class="stub-select" :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"><slot /></select>',
          },
          'el-option': { template: '<option class="stub-option" />' },
        },
        directives: { loading: {} },
      },
    })
  }

  /** 等配置到位再断言，避免与取数竞态 */
  async function mountLoaded() {
    const wrapper = mountPage()
    await vi.waitFor(() => expect(wrapper.text()).toContain('tap_screen'))
    await nextTick()
    return wrapper
  }

  it('三层结构可见：角色带 / 生效装配 / 参考数据 + 右栏对话', async () => {
    const wrapper = await mountLoaded()

    expect(wrapper.find('.md-role').exists()).toBe(true)
    expect(wrapper.find('.md-role-name').text()).toBe('执行模型 Executor')
    const facts = wrapper.find('.md-facts').text()
    expect(facts).toContain('deepseek-chat')
    expect(facts).toContain('deepseek')
    expect(facts).toContain('多模态（可读截图）')
    expect(facts).toContain('2/3 启用')
    expect(facts).toContain('1 个')
    expect(facts).toContain('1 份文档')

    const text = wrapper.text()
    expect(text).toContain('① 生效装配 · 能干什么')
    expect(text).toContain('② 参考数据 · 有哪些资产')
    expect(text).toContain('③ 调试对话 · 常驻右栏')
    expect(wrapper.find('.md-chat .md-textarea').exists()).toBe(true)
  })

  it('工具按分类分组，组头显示启用数与总数', async () => {
    const wrapper = await mountLoaded()

    const groups = wrapper.findAll('.md-group-sub')
    expect(groups.map((node) => node.text())).toEqual([
      '设备控制 · 2/2 启用',
      '设备检查器 · 0/1 启用',
    ])
    expect(wrapper.find('.md-group-head').text()).toContain('2/3 启用')
    expect(wrapper.text()).toContain('已停用')
    expect(wrapper.text()).toContain('只读')
  })

  it('提示词默认折叠，展开后才渲染 Markdown 正文', async () => {
    const wrapper = await mountLoaded()

    expect(wrapper.find('.md-md').exists()).toBe(false)
    const toggle = wrapper.find('.md-group-head--toggle')
    expect(toggle.text()).toContain(String(CONFIG.data.role.prompt.length) + ' 字')
    expect(toggle.text()).toContain('库中当前值')

    await toggle.trigger('click')
    await nextTick()

    expect(wrapper.find('.md-md').exists()).toBe(true)
    expect(wrapper.find('.md-md').text()).toContain('EXECUTOR-PROMPT')
  })

  it('两条归属标注出现在对应区块的组头内', async () => {
    const wrapper = await mountLoaded()

    const heads = wrapper.findAll('.md-group-head')
    const skillHead = heads.find((node) => node.text().includes('Skill'))
    const kbHead = heads.find((node) => node.text().includes('知识库'))
    expect(skillHead?.text()).toContain(SKILL_SHARED_NOTE)
    expect(kbHead?.text()).toContain(KNOWLEDGE_RAG_NOTE)
    expect(wrapper.text()).toContain('a.md')
  })

  it('角色分段项可点：push 同页不同 role 参数，当前角色不重复 push', async () => {
    const wrapper = await mountLoaded()

    const tabs = wrapper.findAll('.md-tab')
    expect(tabs.map((node) => node.text())).toEqual(['规划模型', '执行模型', '验收模型'])

    await tabs[0].trigger('click')
    expect(routerPush).toHaveBeenCalledWith('/ai-assistant/toolbox/models/planner')

    await tabs[1].trigger('click')
    expect(routerPush).toHaveBeenCalledTimes(1)
  })

  /** 选设备 → 确认 → 发送，并等到消息条数到位（需要设备的角色走完整链路） */
  async function sendText(
    wrapper: VueWrapper,
    text: string,
    expectedMessages: number,
  ): Promise<void> {
    await wrapper.find('.stub-select').setValue('ONLINE-1')
    await wrapper.find('.md-textarea').setValue(text)
    confirmMock.mockResolvedValue(undefined)
    await wrapper.find('.md-chat-actions .md-btn--primary').trigger('click')
    await vi.waitFor(() => expect(wrapper.findAll('.md-msg')).toHaveLength(expectedMessages))
  }

  /** 助手回复带思考过程时的返回体 */
  function replyWithThinking(reply: string) {
    return {
      status: true,
      data: {
        role: 'executor',
        label: '执行模型',
        model_name: 'deepseek-chat',
        reply,
        thinking: ['先看需求', '再拆步骤'],
      },
    }
  }

  it('对话框可发送并渲染回复', async () => {
    chat.mockResolvedValue({
      status: true,
      data: { role: 'executor', label: '执行模型', model_name: 'deepseek-chat', reply: 'PLAN-OK' },
    })
    const wrapper = await mountLoaded()

    await sendText(wrapper, '把需求拆成步骤', 2)

    expect(chat).toHaveBeenCalledWith('executor', '把需求拆成步骤', 'ONLINE-1')
    expect(wrapper.text()).toContain('PLAN-OK')
  })

  it('助手消息把返回结果与思考过程分成两个带标题的区块', async () => {
    chat.mockResolvedValue(replyWithThinking('PLAN-OK'))
    const wrapper = await mountLoaded()

    await sendText(wrapper, '把需求拆成步骤', 2)

    const answer = wrapper.findAll('.md-msg')[1]
    expect(answer.find('.md-answer-label').text()).toBe(MODEL_DEBUG_ANSWER_LABEL)
    expect(answer.find('.md-answer .md-msg-text').text()).toBe('PLAN-OK')
    expect(answer.find('.md-think-title').text()).toBe(MODEL_DEBUG_THINKING_LABEL)
    expect(answer.find('.md-think-meta').text()).toContain('字')
    // 默认展开：思考正文立即可见
    expect(answer.find('.md-think-body').text()).toContain('先看需求')
  })

  it('思考过程可收起再展开，收起时回复仍在', async () => {
    chat.mockResolvedValue(replyWithThinking('PLAN-OK'))
    const wrapper = await mountLoaded()

    await sendText(wrapper, '把需求拆成步骤', 2)

    const answer = wrapper.findAll('.md-msg')[1]
    await answer.find('.md-think-head').trigger('click')
    expect(answer.find('.md-think-body').exists()).toBe(false)
    expect(answer.find('.md-answer .md-msg-text').text()).toBe('PLAN-OK')

    await answer.find('.md-think-head').trigger('click')
    expect(answer.find('.md-think-body').text()).toContain('先看需求')
  })

  it('折叠状态逐条消息独立', async () => {
    chat.mockResolvedValue(replyWithThinking('PLAN-OK'))
    const wrapper = await mountLoaded()

    await sendText(wrapper, '第一问', 2)
    await sendText(wrapper, '第二问', 4)

    const first = wrapper.findAll('.md-msg')[1]
    const second = wrapper.findAll('.md-msg')[3]
    await second.find('.md-think-head').trigger('click')

    expect(second.find('.md-think-body').exists()).toBe(false)
    expect(first.find('.md-think-body').exists()).toBe(true)
  })

  it('无思考过程时不渲染思考区块', async () => {
    chat.mockResolvedValue({
      status: true,
      data: { role: 'executor', label: '执行模型', model_name: 'deepseek-chat', reply: 'PLAIN' },
    })
    const wrapper = await mountLoaded()

    await sendText(wrapper, '把需求拆成步骤', 2)

    const answer = wrapper.findAll('.md-msg')[1]
    expect(answer.find('.md-think').exists()).toBe(false)
    expect(answer.find('.md-answer-label').text()).toBe(MODEL_DEBUG_ANSWER_LABEL)
  })

  it('调用失败时结果区块标题为「调用失败」', async () => {
    chat.mockResolvedValue({ status: false, message: '「执行模型 Executor」的 api_key 未配置' })
    const wrapper = await mountLoaded()

    await sendText(wrapper, '把需求拆成步骤', 2)

    const answer = wrapper.findAll('.md-msg')[1]
    expect(answer.find('.md-answer-label').text()).toBe(MODEL_DEBUG_ANSWER_ERROR_LABEL)
    expect(answer.find('.md-msg-text').text()).toContain('api_key 未配置')
    expect(answer.find('.md-think').exists()).toBe(false)
  })

  it('需要设备的角色：渲染设备下拉，未选设备不能发送', async () => {
    const wrapper = await mountLoaded()

    expect(wrapper.find('.md-device').exists()).toBe(true)
    expect(wrapper.find('.stub-select').exists()).toBe(true)

    await wrapper.find('.md-textarea').setValue('跑一下')
    expect(wrapper.find('.md-chat-actions .md-btn--primary').attributes('disabled')).toBeDefined()

    await wrapper.find('.stub-select').setValue('ONLINE-1')
    expect(wrapper.find('.md-chat-actions .md-btn--primary').attributes('disabled')).toBeUndefined()
  })

  it('发送前二次确认：写明目标设备与写工具数量，确认后才调用', async () => {
    chat.mockResolvedValue(replyWithThinking('OK'))
    const wrapper = await mountLoaded()

    await sendText(wrapper, '跑一下', 2)

    expect(confirmMock).toHaveBeenCalledTimes(1)
    const text = String(confirmMock.mock.calls[0][0])
    expect(text).toContain('SM-S9010')
    expect(text).toContain('2 个写工具')
    expect(chat).toHaveBeenCalledWith('executor', '跑一下', 'ONLINE-1')
  })

  it('取消二次确认则不发起调用', async () => {
    chat.mockResolvedValue(replyWithThinking('OK'))
    const wrapper = await mountLoaded()

    await wrapper.find('.stub-select').setValue('ONLINE-1')
    await wrapper.find('.md-textarea').setValue('跑一下')
    confirmMock.mockRejectedValue(new Error('cancel'))
    await wrapper.find('.md-chat-actions .md-btn--primary').trigger('click')
    await nextTick()

    expect(confirmMock).toHaveBeenCalledTimes(1)
    expect(chat).not.toHaveBeenCalled()
    expect(wrapper.findAll('.md-msg')).toHaveLength(0)
  })

  it('助手消息展示工具调用轨迹与读写徽标', async () => {
    chat.mockResolvedValue({
      status: true,
      data: {
        role: 'executor',
        label: '执行模型',
        model_name: 'deepseek-chat',
        reply: 'OK',
        tool_usage: [
          { type: 'call', name: 'tap_screen', input: { serial: 'ONLINE-1' } },
          { type: 'result', name: 'tap_screen', state: 'success', output: 'ok' },
        ],
      },
    })
    const wrapper = await mountLoaded()

    await sendText(wrapper, '点一下', 2)

    const answer = wrapper.findAll('.md-msg')[1]
    expect(answer.find('.md-trace-title').text()).toBe(MODEL_DEBUG_TRACE_LABEL)
    expect(answer.findAll('.md-trace-item')).toHaveLength(2)
    expect(answer.find('.md-trace-item .md-badge').text()).toBe('写')
    expect(answer.find('.md-trace-name').text()).toBe('tap_screen')
  })

  it('页面如实描述行为，不再声明旧限制', async () => {
    const wrapper = await mountLoaded()

    const text = wrapper.text()
    expect(text).toContain(MODEL_DEBUG_SCOPE_NOTE)
    expect(text).not.toContain('最长 5 分钟')
    expect(text).not.toContain('不挂工具')
    expect(text).not.toContain('不碰真机')
  })
})
