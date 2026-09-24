import { describe, expect, it } from 'vitest'
import { formatPlannerInputText } from '@/modules/ai-assistant/helpers/task-detail'

describe('formatPlannerInputText', () => {
  it('紧凑单行四键展开为缩进 JSON 代码块，键顺序不变', () => {
    const raw =
      '{"任务标题":"打开应用","任务目标":"启动 govee 并进入列表","附件文本内容":"","设备ID":"ABC123"}'
    expect(formatPlannerInputText(raw)).toBe(
      [
        '{',
        '  "任务标题": "打开应用",',
        '  "任务目标": "启动 govee 并进入列表",',
        '  "附件文本内容": "",',
        '  "设备ID": "ABC123"',
        '}',
      ].join('\n'),
    )
  })

  it('字符串内的 \\n 呈现为真实换行并与该值同层级缩进', () => {
    const raw = '{"任务目标":"第一行\\n第二行\\n第三行"}'
    expect(formatPlannerInputText(raw)).toBe(
      ['{', '  "任务目标": "第一行', '  第二行', '  第三行"', '}'].join('\n'),
    )
  })

  it('附件正文的 CRLF 归一为换行，引号与反斜杠按 JSON 规则转义', () => {
    const raw = '{"附件文本内容":"# 标题\\r\\n\\r\\n- 项 \\"A\\"\\\\B"}'
    expect(formatPlannerInputText(raw)).toBe(
      ['{', '  "附件文本内容": "# 标题', '', '  - 项 \\"A\\"\\\\B"', '}'].join('\n'),
    )
  })

  it('嵌套对象与数组逐层缩进', () => {
    const raw = '{"steps":[{"action":"点按","assert":"出现列表"}]}'
    expect(formatPlannerInputText(raw)).toBe(
      [
        '{',
        '  "steps": [',
        '    {',
        '      "action": "点按",',
        '      "assert": "出现列表"',
        '    }',
        '  ]',
        '}',
      ].join('\n'),
    )
  })

  it('非 JSON 文本原样回退，不丢内容不报错', () => {
    expect(formatPlannerInputText('  {不是 JSON 的文本  ')).toBe('{不是 JSON 的文本')
  })

  it('空值与全空白返回空串（交由调用方走空态）', () => {
    expect(formatPlannerInputText()).toBe('')
    expect(formatPlannerInputText('')).toBe('')
    expect(formatPlannerInputText('   \n  ')).toBe('')
  })
})
