/**
 * [P0] 必测 — 执行引擎占用判定（前缀清单唯一登记处）
 * 目录：tests/shared/p0/
 *
 * 两种粒度都要锁定：设备卡 / 操作列只看前缀（isRunnerOccupied），
 * 状态列与设备检查器还要求 status=BUSY（isExecutionOccupied）。
 */
import { describe, expect, it } from 'vitest'
import {
  RUNNER_OCCUPIED_PREFIXES,
  isExecutionOccupied,
  isRunnerOccupied,
} from '@/shared/helpers/deviceOccupancy'

describe('[P0] shared/deviceOccupancy', () => {
  it('BUSY + 执行引擎前缀：每个已登记前缀都判为被执行引擎占用', () => {
    for (const prefix of RUNNER_OCCUPIED_PREFIXES) {
      expect(isExecutionOccupied({ status: 'BUSY', occupied_by: `${prefix}7` })).toBe(true)
    }
  })

  it('BUSY + 非执行引擎占用者：不算执行引擎占用（走人工占用态）', () => {
    expect(isExecutionOccupied({ status: 'BUSY', occupied_by: 'alice' })).toBe(false)
    expect(isRunnerOccupied('alice')).toBe(false)
  })

  it('非 BUSY：即使占用者带执行引擎前缀也不算（占用判定要求 BUSY）', () => {
    expect(isExecutionOccupied({ status: 'ONLINE', occupied_by: 'runner-1' })).toBe(false)
    expect(isExecutionOccupied({ status: 'OFFLINE', occupied_by: 'ai_agent' })).toBe(false)
    expect(isRunnerOccupied('runner-1')).toBe(true)
  })

  it('occupied_by 缺失：两种判定都为假', () => {
    expect(isRunnerOccupied(undefined)).toBe(false)
    expect(isRunnerOccupied('')).toBe(false)
    expect(isExecutionOccupied({ status: 'BUSY' })).toBe(false)
  })

  it('前缀只匹配开头：占用者中段出现前缀不算', () => {
    expect(isRunnerOccupied('run-42')).toBe(true)
    expect(isRunnerOccupied('my-run-42')).toBe(false)
  })
})
