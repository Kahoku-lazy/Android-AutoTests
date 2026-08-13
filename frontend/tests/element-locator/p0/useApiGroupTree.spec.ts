/**
 * [P0] 必测 — API 分组树 composable（__ungrouped__ 映射 / 批量移动归一化 / 扁平→嵌套）
 * 目录：tests/element-locator/p0/
 *
 * 与 useWebGroupTree 同构：共享 helpers/treeGroupFixtures.ts 参数化用例工厂；
 * 本文件只 mock element-plus 与模块 api 的 api 组函数，一行调用 describeGroupTree('api')。
 */
import { vi } from 'vitest'
import { describeGroupTree } from '../helpers/treeGroupFixtures'

vi.mock('element-plus', () => ({
  ElMessage: { success: vi.fn(), warning: vi.fn(), error: vi.fn(), info: vi.fn() },
  ElMessageBox: { confirm: vi.fn() },
}))
vi.mock('@/modules/element-locator/api', () => ({
  apiListApiGroups: vi.fn(),
  apiCreateApiGroup: vi.fn(),
  apiUpdateApiGroup: vi.fn(),
  apiDeleteApiGroup: vi.fn(),
  apiListApiEndpoints: vi.fn(),
  apiBatchMoveApiGroups: vi.fn(),
}))

describeGroupTree('api')
