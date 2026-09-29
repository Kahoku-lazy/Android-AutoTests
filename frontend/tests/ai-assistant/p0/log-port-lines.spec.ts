import { describe, expect, it } from 'vitest'
import {
  LOG_DISABLE_WARNING,
  LOG_TAIL_OPTIONS,
  clockOf,
  decorateLogLines,
  formatLogSize,
  logConclusionText,
  logCountText,
} from '@/modules/ai-assistant/helpers/log-port-lines'
import type { LogPortLine } from '@/modules/ai-assistant/api/toolbox'

const MERGED: LogPortLine[] = [
  { timestamp: '2026-09-28 15:47:42.466', source: 'tcp', text: 'later' },
  {
    timestamp: '2026-09-28 15:47:41.466',
    source: 'tcp',
    text: 'first\nsecond\nthird',
  },
]

describe('log-port-lines display helpers', () => {
  it('keeps the server order and never re-sorts (newest first stays newest first)', () => {
    const decorated = decorateLogLines(MERGED)
    expect(decorated.map((item) => item.timestamp)).toEqual([
      '2026-09-28 15:47:42.466',
      '2026-09-28 15:47:41.466',
    ])
    expect(decorated.map((item) => item.clock)).toEqual(['15:47:42.466', '15:47:41.466'])
  })

  it('preserves the merged entry newlines and flags it as merged', () => {
    const decorated = decorateLogLines(MERGED)
    expect(decorated[1].text).toBe('first\nsecond\nthird')
    expect(decorated[1].text.split('\n')).toEqual(['first', 'second', 'third'])
    expect(decorated[1].merged).toBe(true)
    expect(decorated[0].merged).toBe(false)
  })

  it('tolerates empty and partial input', () => {
    expect(decorateLogLines([])).toEqual([])
    expect(decorateLogLines(undefined as unknown as LogPortLine[])).toEqual([])
    const [only] = decorateLogLines([{ timestamp: '', source: '', text: '' }])
    expect(only.clock).toBe('')
    expect(only.key).toBe('#0')
  })

  it('maps conclusions to readable Chinese text', () => {
    expect(logConclusionText('ok', 7005)).toBe('')
    expect(logConclusionText('no_log', 7005)).toContain('暂无内容')
    expect(logConclusionText('port_disabled', 7005)).toBe('端口 7005 已关闭监听')
    expect(logConclusionText('port_not_configured', 7004)).toBe('端口 7004 未配置为日志来源')
  })

  it('summarizes counts and file size', () => {
    expect(logCountText(0, 0)).toBe('0 条')
    expect(logCountText(2, 3)).toContain('2 条（原始 3 行')
    expect(logCountText(3, 3)).toBe('3 条')
    expect(formatLogSize(512)).toBe('512 B')
    expect(formatLogSize(2048)).toBe('2.0 KB')
    expect(formatLogSize(50 * 1024 * 1024)).toBe('50.0 MB')
  })

  it('exposes tail options and the disable warning copy', () => {
    expect(LOG_TAIL_OPTIONS).toContain(2000)
    expect(LOG_DISABLE_WARNING).toContain('AI 设备任务验收')
  })

  it('splits the clock part out of a full timestamp', () => {
    expect(clockOf('2026-09-28 15:47:41.466')).toBe('15:47:41.466')
    expect(clockOf('15:47:41.466')).toBe('15:47:41.466')
  })
})
