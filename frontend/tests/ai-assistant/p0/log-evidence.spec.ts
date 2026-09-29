/**
 * [P0] 必测 — 任务详情「验收设备日志证据」展示口径
 * 目录：tests/ai-assistant/p0/
 */
import { describe, expect, it } from 'vitest'
import {
  NO_EVIDENCE_TEXT,
  conclusionText,
  evidenceLines,
  evidenceSummary,
  featureText,
  gradeLabel,
  gradeTagClass,
  hasEvidenceDetail,
  hitFeatureText,
  hitOccurrences,
  outOfWindowLine,
  windowHint,
} from '@/modules/ai-assistant/helpers/log-evidence'
import type { TaskLogEvidence } from '@/shared/types/ai'

const MERGED_TEXT = 'request\nstart\nswitch_off'

const EVIDENCE: TaskLogEvidence = {
  channel: 'H6810',
  window_id: 'w3',
  window_opened_at: '2026-09-28 15:47:40.000',
  action_time: '2026-09-28 15:47:41.466',
  action_times: ['2026-09-28 15:47:41.466'],
  threshold_seconds: 5,
  baseline_seconds: 30,
  window_line_count: 3,
  conclusion: 'hit',
  hits: [
    {
      keyword: 'switch_off',
      grade: 'strong',
      count: 1,
      timestamps: ['2026-09-28 15:47:41.810'],
      occurrences: [
        { timestamp: '2026-09-28 15:47:41.810', source: 'tcp', text: '[light_switch][I]: switch_off' },
      ],
      features: [{ id: 1, module: '设备开关', feature: '关闭设备成功' }],
    },
  ],
  before_action: [],
  out_of_window: [],
  lines: [
    { timestamp: '2026-09-28 15:47:42.466', source: 'tcp', text: 'later' },
    { timestamp: '2026-09-28 15:47:41.466', source: 'tcp', text: MERGED_TEXT },
  ],
}

describe('[P0] log-evidence 等级与结论口径', () => {
  it('四个等级都有中文标签与配色类', () => {
    expect(gradeLabel('strong')).toBe('强证据')
    expect(gradeLabel('periodic')).toBe('疑似周期')
    expect(gradeLabel('before_action')).toBe('动作前')
    expect(gradeLabel('out_of_window')).toBe('超窗')
    expect(gradeTagClass('strong')).toBe('sle-tag--strong')
    expect(gradeTagClass('periodic')).toBe('sle-tag--periodic')
    expect(gradeTagClass('before_action')).toBe('sle-tag--before')
    expect(gradeTagClass('out_of_window')).toBe('sle-tag--out')
  })

  it('未知等级与缺省不抛错', () => {
    expect(gradeLabel('weird')).toBe('weird')
    expect(gradeLabel(undefined)).toBe('未知等级')
    expect(gradeTagClass(undefined)).toBe('sle-tag--out')
  })

  it('结论文案覆盖四种取值', () => {
    expect(conclusionText('hit')).toContain('命中')
    expect(conclusionText('no_hit')).toContain('未命中')
    expect(conclusionText('no_log')).toContain('没有日志')
    expect(conclusionText('out_of_window')).toContain('超窗')
    expect(conclusionText('')).toBe('')
  })

  it('功能点文案带编号与模块，信息不全时降级', () => {
    expect(featureText({ id: 1, module: '设备开关', feature: '关闭设备成功' })).toBe(
      '关闭设备成功（#1 设备开关）',
    )
    expect(featureText({ feature: '关闭设备成功' })).toBe('关闭设备成功')
    expect(featureText({ id: 2, module: '灯效库' })).toBe('#2 灯效库')
    expect(featureText(undefined)).toBe('未登记功能点')
  })
})

describe('[P0] log-evidence 摘要', () => {
  it('命中时给出等级、条数、关键词与功能点', () => {
    const text = evidenceSummary(EVIDENCE)
    expect(text).toContain('强证据 1 条')
    expect(text).toContain('switch_off')
    expect(text).toContain('关闭设备成功（#1 设备开关）')
  })

  it('疑似周期被显式标出', () => {
    const periodic: TaskLogEvidence = {
      conclusion: 'hit',
      hits: [{ keyword: 'lumi_set_success', grade: 'periodic', count: 2 }],
    }
    expect(evidenceSummary(periodic)).toContain('疑似周期 2 条')
  })

  it('多条命中全部列出（不省略）', () => {
    const multi: TaskLogEvidence = {
      conclusion: 'hit',
      hits: [
        { keyword: 'switch_on', grade: 'strong', count: 1 },
        { keyword: 'switch_off', grade: 'strong', count: 1 },
      ],
    }
    const text = evidenceSummary(multi)
    expect(text).toContain('switch_on')
    expect(text).toContain('switch_off')
  })

  it('无命中时给出结论与窗口行数', () => {
    expect(evidenceSummary({ conclusion: 'no_hit', window_line_count: 3 })).toBe(
      '有日志但未命中关键词（窗口内 3 行）',
    )
    expect(evidenceSummary({ conclusion: 'no_log', window_line_count: 0 })).toContain('没有日志')
    expect(evidenceSummary({})).toBe('窗口内没有日志')
  })

  it('没有证据对象时摘要为空（由组件走说明行）', () => {
    expect(evidenceSummary(undefined)).toBe('')
    expect(evidenceSummary(null)).toBe('')
  })
})

describe('[P0] log-evidence 详情取值（不重排）', () => {
  it('窗口日志按入参顺序返回，不做排序', () => {
    const lines = evidenceLines(EVIDENCE)
    expect(lines.map((l) => l.timestamp)).toEqual([
      '2026-09-28 15:47:42.466',
      '2026-09-28 15:47:41.466',
    ])
  })

  it('合并条保留内部换行并标记 merged', () => {
    const lines = evidenceLines(EVIDENCE)
    expect(lines[1].text.split('\n')).toEqual(['request', 'start', 'switch_off'])
    expect(lines[1].merged).toBe(true)
    expect(lines[0].merged).toBe(false)
  })

  it('命中原文优先 occurrences，缺失时退回时间戳', () => {
    const withOcc = hitOccurrences(EVIDENCE.hits?.[0])
    expect(withOcc).toHaveLength(1)
    expect(withOcc[0].text).toContain('switch_off')

    const onlyStamps = hitOccurrences({ timestamps: ['2026-09-28 15:47:41.810'] })
    expect(onlyStamps).toEqual([
      { timestamp: '2026-09-28 15:47:41.810', text: '', source: '' },
    ])
    expect(hitOccurrences(undefined)).toEqual([])
  })

  it('超窗行带延迟秒数', () => {
    expect(outOfWindowLine({ timestamp: 'T', text: 'x', delta_seconds: 14.3094 })).toBe(
      'T · +14.309s · x',
    )
    expect(outOfWindowLine({ text: 'x' })).toBe('x')
  })

  it('有详情才算可折叠；空证据不可折叠', () => {
    expect(hasEvidenceDetail(EVIDENCE)).toBe(true)
    expect(hasEvidenceDetail({ conclusion: 'no_log', window_line_count: 0 })).toBe(false)
    expect(hasEvidenceDetail(undefined)).toBe(false)
  })

  it('窗口参数文案与无证据说明', () => {
    expect(windowHint(EVIDENCE)).toContain('取证窗 5 秒')
    expect(windowHint(EVIDENCE)).toContain('动作前基线 30 秒')
    expect(windowHint(undefined)).toBe('')
    expect(NO_EVIDENCE_TEXT).toContain('未采集到设备日志证据')
  })

  it('字段缺失的脏数据不抛错', () => {
    expect(evidenceLines({ lines: [{}, { text: 'x' }] })).toEqual([
      { timestamp: '', source: '', text: '', merged: false },
      { timestamp: '', source: '', text: 'x', merged: false },
    ])
    expect(hitFeatureText({})).toBe('')
    expect(evidenceSummary({ hits: [{ grade: 'strong' }] })).toContain('强证据')
  })
})
