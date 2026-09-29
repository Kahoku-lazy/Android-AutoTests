/**
 * [P0] 必测 — 日志关键词表格行与搜索（spec: device-log-keyword-catalog）
 *
 * 目录：tests/ai-assistant/p0/
 * 断言：① 表内顺序（关键词按表内先后、功能点按表内先后，前端不重排）；
 * ② 一个关键词对应多个功能点 → 多行；③ 计数口径（关键词去重、功能点按模块+编号+名称去重）；
 * ④ 搜索覆盖关键词 / 模块 / 功能点，清空回全量；⑤ 缺名占位不丢行。
 */
import { describe, expect, it } from 'vitest'
import {
  UNNAMED_FEATURE,
  UNNAMED_MODULE,
  buildKeywordRows,
  filterKeywordRows,
  keywordRowCounts,
} from '@/modules/ai-assistant/helpers/log-keyword-rows'
import type { LogKeywordEntry } from '@/modules/ai-assistant/api/toolbox'

const ENTRIES: LogKeywordEntry[] = [
  { keyword: 'switch_on', features: [{ id: 0, module: '设备开关', feature: '打开设备成功' }] },
  {
    keyword: 'color_configs_set_success',
    features: [
      { id: 2, module: '音效律动', feature: '灯光颜色设置成功' },
      { id: 17, module: '彩色模式', feature: '手动-颜色设置成功' },
    ],
  },
  { keyword: 'switch_off', features: [{ id: 1, module: '设备开关', feature: '关闭设备成功' }] },
]

describe('[P0] buildKeywordRows', () => {
  it('一行一个「关键词 × 功能点」，顺序与表内一致', () => {
    const rows = buildKeywordRows(ENTRIES)
    expect(rows.map((r) => [r.keyword, r.featureId])).toEqual([
      ['switch_on', 0],
      ['color_configs_set_success', 2],
      ['color_configs_set_success', 17],
      ['switch_off', 1],
    ])
    expect(rows[0]).toMatchObject({ module: '设备开关', featureName: '打开设备成功' })
  })

  it('行标识唯一（同关键词不同功能点不冲突）', () => {
    const keys = buildKeywordRows(ENTRIES).map((r) => r.key)
    expect(new Set(keys).size).toBe(keys.length)
  })

  it('缺模块 / 缺功能点名给占位，不丢行', () => {
    const rows = buildKeywordRows([{ keyword: 'x', features: [{ id: 1 }] }])
    expect(rows.length).toBe(1)
    expect(rows[0].module).toBe(UNNAMED_MODULE)
    expect(rows[0].featureName).toBe(UNNAMED_FEATURE)
  })

  it('关键词为空的条目跳过', () => {
    expect(buildKeywordRows([{ keyword: '  ', features: [{ id: 1 }] }])).toEqual([])
  })

  it('计数按去重口径：关键词去重、功能点按模块+编号+名称去重', () => {
    const counts = keywordRowCounts(buildKeywordRows(ENTRIES))
    expect(counts.keywords).toBe(3)
    expect(counts.features).toBe(4)
  })
})

describe('[P0] filterKeywordRows', () => {
  const rows = buildKeywordRows(ENTRIES)

  it('空查询返回全量', () => {
    expect(filterKeywordRows(rows, '   ')).toEqual(rows)
  })

  it('按关键词搜索（忽略大小写，多功能点的行都在）', () => {
    const hit = filterKeywordRows(rows, 'COLOR_CONFIGS')
    expect(hit.length).toBe(2)
    expect(hit.map((r) => r.featureId)).toEqual([2, 17])
  })

  it('按功能点名搜索', () => {
    expect(filterKeywordRows(rows, '定时')).toEqual([])
    expect(filterKeywordRows(rows, '关闭设备').map((r) => r.keyword)).toEqual(['switch_off'])
  })

  it('按模块名搜索', () => {
    expect(filterKeywordRows(rows, '设备开关').length).toBe(2)
  })

  it('无命中返回空数组', () => {
    expect(filterKeywordRows(rows, 'zzz-not-exist')).toEqual([])
  })
})
