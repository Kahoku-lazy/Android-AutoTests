/**
 * [P0] 报告工作台列与空态文案（任务卡数据源，不跳转详情）
 */
import { describe, expect, it } from 'vitest'
import { EMPTY_TEXT, PAGE_HEADER, TABLE_COLUMNS } from '@/modules/report-generator/constants'

describe('[P0] report-generator workbench copy', () => {
  it('table columns are task-card fields without case metrics', () => {
    expect(TABLE_COLUMNS.map((c) => c.dataIndex)).toEqual([
      'run_id',
      'device_serial',
      'task_name',
      'creator',
      'status',
      'duration',
      'started_at',
    ])
    expect(TABLE_COLUMNS.some((c) => ['case_count', 'passed', 'failed', 'rate'].includes(c.dataIndex))).toBe(false)
  })

  it('empty copy points to AI assistant and not the execution engine', () => {
    expect(PAGE_HEADER.subtitle).toContain('AI 助手')
    expect(EMPTY_TEXT.hint).toContain('AI 助手')
    expect(EMPTY_TEXT.hint).not.toContain('执行引擎')
    expect(EMPTY_TEXT.noData).not.toContain('执行引擎')
  })
})
