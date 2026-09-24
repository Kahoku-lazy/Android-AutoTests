/**
 * [P0] 任务详情「送给规划模型的输入」：缩进 JSON 代码块 + 字符串内真实换行
 */
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import TaskInputPanel from '@/modules/ai-assistant/components/TaskInputPanel.vue'

const STUBS = {
  EmptyState: true,
  'el-collapse': { template: '<div><slot /></div>' },
  'el-collapse-item': { template: '<div><slot name="title" /><slot /></div>' },
}

function mountPanel(props: Record<string, unknown>) {
  return mount(TaskInputPanel, { props, global: { stubs: STUBS } })
}

describe('TaskInputPanel 规划输入呈现', () => {
  it('四键按行展开，字符串内的换行按真实换行显示', () => {
    const raw =
      '{"任务标题":"打开应用","任务目标":"第一步\\n第二步","附件文本内容":"# 标题\\n\\n- 项","设备ID":"ABC123"}'
    const pre = mountPanel({ plannerInput: raw }).find('pre.ti-pre')
    const text = pre.text()

    expect(text.startsWith('{\n  "任务标题": "打开应用",')).toBe(true)
    expect(text).toContain('  "任务目标": "第一步\n  第二步",')
    expect(text).toContain('  "附件文本内容": "# 标题\n\n  - 项",')
    expect(text.endsWith('\n  "设备ID": "ABC123"\n}')).toBe(true)
    expect(text).not.toContain('\\n')
  })

  it('非 JSON 文本原样展示，不丢内容', () => {
    const pre = mountPanel({ plannerInput: '不是 JSON 的文本' }).find('pre.ti-pre')
    expect(pre.text()).toBe('不是 JSON 的文本')
  })

  it('无规划输入时走空态，不渲染空代码块', () => {
    const w = mountPanel({})
    expect(w.find('pre.ti-pre').exists()).toBe(false)
    expect(w.text()).toContain('本条任务没有规划输入记录')
  })
})
