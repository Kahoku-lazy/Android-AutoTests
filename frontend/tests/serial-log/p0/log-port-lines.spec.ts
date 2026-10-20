import { describe, expect, it } from 'vitest'
import {
  LOG_DISABLE_WARNING,
  LOG_TAIL_OPTIONS,
  decorateLogLines,
  formatLogSize,
  logConclusionText,
  logCountText,
} from '@/modules/serial-log/helpers/log-port-lines'
import type { LogPortLine } from '@/modules/serial-log/api'

const RAW: LogPortLine[] = [
  { text: '2026-09-28 15:47:41,466 - uart.H6810.7005 - INFO - first' },
  { text: '2026-09-28 15:47:42,466 - uart.H6810.7005 - INFO - later' },
]

describe('log-port-lines display helpers', () => {
  it('keeps the server order and shows the whole line', () => {
    const decorated = decorateLogLines(RAW)
    expect(decorated.map((item) => item.text)).toEqual([
      '2026-09-28 15:47:41,466 - uart.H6810.7005 - INFO - first',
      '2026-09-28 15:47:42,466 - uart.H6810.7005 - INFO - later',
    ])
  })

  it('tolerates empty and partial input', () => {
    expect(decorateLogLines([])).toEqual([])
    expect(decorateLogLines(undefined as unknown as LogPortLine[])).toEqual([])
    const [only] = decorateLogLines([{ text: '' }])
    expect(only.text).toBe('')
    expect(only.key).toBe('0')
  })

  it('maps conclusions to readable Chinese text', () => {
    expect(logConclusionText('ok', 7005)).toBe('')
    expect(logConclusionText('no_log', 7005)).toContain('暂无内容')
    expect(logConclusionText('port_disabled', 7005)).toBe('端口 7005 已关闭监听')
    expect(logConclusionText('port_not_configured', 7004)).toBe('端口 7004 未配置为日志来源')
  })

  it('summarizes counts and file size', () => {
    expect(logCountText(0, 0)).toBe('0 条')
    expect(logCountText(3, 3)).toBe('3 条')
    expect(formatLogSize(512)).toBe('512 B')
    expect(formatLogSize(2048)).toBe('2.0 KB')
    expect(formatLogSize(50 * 1024 * 1024)).toBe('50.0 MB')
  })

  it('exposes tail options and the disable warning copy', () => {
    expect(LOG_TAIL_OPTIONS).toContain(2000)
    expect(LOG_DISABLE_WARNING).toContain('不再监听该端口')
  })
})
