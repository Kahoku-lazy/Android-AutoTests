/**
 * [P0] 共享夹具 — Web/API 分组树参数化用例工厂
 * 目录：tests/element-locator/helpers/
 *
 * useWebGroupTree / useApiGroupTree 两棵分组树同构（仅 api 函数名与列表字段不同），
 * 由 describeGroupTree('web' | 'api') 各跑一遍同一套用例：
 *   1. selectGroup('__ungrouped__')：参数映射为 { group_id: 'null' }
 *   2. confirmBatchMove：目标 '__root__' 归一化为 parent_id null
 *   3. loadGroups：扁平列表转嵌套树，孤儿归根
 * wrapper 统一在 afterEach unmount，断言失败不泄漏 window click 监听。
 * 依赖调用方 spec 完成 vi.mock（element-plus + 模块 api），本文件不断真网络。
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, type VueWrapper } from '@vue/test-utils'
import * as elApi from '@/modules/element-locator/api'
import { useWebGroupTree } from '@/modules/element-locator/composables/useWebGroupTree'
import { useApiGroupTree } from '@/modules/element-locator/composables/useApiGroupTree'
import { mountComposable } from '../../helpers/mountComposable'

type ModuleName = 'web' | 'api'
type GroupNode = Record<string, any>

/** 两棵树共用的最小行为面（夹具只测共享点，其余成员不涉及） */
interface GroupTreeApi {
  groupTree: { value: GroupNode[] }
  selectedGroup: { value: GroupNode | null }
  selectedGroupIds: Set<number>
  moveTargetDirId: { value: string | null }
  selectGroup: (groupOrNull: GroupNode | null) => Promise<void>
  confirmBatchMove: () => Promise<void>
}

interface ModuleConfig {
  /** describe 标题里的 composable 名 */
  composableName: string
  composable: () => unknown
  listGroups: typeof elApi.apiListWebGroups
  listItems: typeof elApi.apiListWebElements
  batchMove: typeof elApi.apiBatchMoveWebGroups
  /** 列表响应字段名：web=elements，api=endpoints */
  itemsKey: 'elements' | 'endpoints'
}

/**
 * 两棵树的配置按分支延迟构建：调用方 spec 的 mock 只提供自己那组 api 函数，
 * 模块级急切访问另一组会触发 vitest「mock 上无此导出」报错。
 */
function buildConfig(moduleName: ModuleName): ModuleConfig {
  return moduleName === 'web'
    ? {
        composableName: 'useWebGroupTree',
        composable: useWebGroupTree,
        listGroups: elApi.apiListWebGroups,
        listItems: elApi.apiListWebElements,
        batchMove: elApi.apiBatchMoveWebGroups,
        itemsKey: 'elements',
      }
    : {
        composableName: 'useApiGroupTree',
        composable: useApiGroupTree,
        listGroups: elApi.apiListApiGroups,
        listItems: elApi.apiListApiEndpoints,
        batchMove: elApi.apiBatchMoveApiGroups,
        itemsKey: 'endpoints',
      }
}

/**
 * 参数化用例工厂：同一套用例跑两棵同构分组树。
 * 调用方 spec 需先 vi.mock('element-plus') 与 vi.mock('@/modules/element-locator/api')。
 */
export function describeGroupTree(moduleName: ModuleName) {
  const cfg = buildConfig(moduleName)
  const mounted: VueWrapper[] = []

  describe(`[P0] element-locator ${cfg.composableName}`, () => {
    beforeEach(() => {
      vi.clearAllMocks()
    })

    afterEach(() => {
      mounted.forEach((w) => w.unmount())
      mounted.length = 0
    })

    async function mountTree(): Promise<GroupTreeApi> {
      const { result, wrapper } = await mountComposable(() => cfg.composable())
      mounted.push(wrapper)
      await flushPromises()
      return result as unknown as GroupTreeApi
    }

    it(`selectGroup：'__ungrouped__' 映射为 { group_id: 'null' }`, async () => {
      vi.mocked(cfg.listGroups).mockResolvedValue({ data: { status: true, groups: [] } } as never)
      vi.mocked(cfg.listItems).mockResolvedValue({ data: { status: true, [cfg.itemsKey]: [] } } as never)
      const result = await mountTree()

      await result.selectGroup({ id: '__ungrouped__', name: '未分组' })

      expect(result.selectedGroup.value?.id).toBe('__ungrouped__')
      expect(cfg.listItems).toHaveBeenCalledWith({ group_id: 'null' })
    })

    it('confirmBatchMove：目标 __root__ 归一化为 parent_id null', async () => {
      vi.mocked(cfg.listGroups).mockResolvedValue({ data: { status: true, groups: [] } } as never)
      vi.mocked(cfg.batchMove).mockResolvedValue({ data: { status: true } } as never)
      const result = await mountTree()

      result.selectedGroupIds.add(1)
      result.moveTargetDirId.value = '__root__'
      await result.confirmBatchMove()

      expect(cfg.batchMove).toHaveBeenCalledWith([1], null)
    })

    it('loadGroups：扁平列表转嵌套树，孤儿归根', async () => {
      vi.mocked(cfg.listGroups).mockResolvedValue({
        data: {
          status: true,
          groups: [
            { id: 1, name: '目录A', is_folder: true, parent_id: null },
            { id: 2, name: '分组B', is_folder: false, parent_id: 1 },
            { id: 3, name: '孤儿C', is_folder: false, parent_id: 99 },
          ],
        },
      } as never)
      const result = await mountTree()

      expect(result.groupTree.value).toHaveLength(2)
      expect(result.groupTree.value[0].id).toBe(1)
      expect(result.groupTree.value[0].children).toHaveLength(1)
      expect(result.groupTree.value[0].children[0].id).toBe(2)
      expect(result.groupTree.value[1].id).toBe(3) // parent_id=99 不存在 → 归根
      expect(result.groupTree.value[1].children).toHaveLength(0)
    })
  })
}
