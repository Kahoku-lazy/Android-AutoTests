/**
 * [P1] 建议测 — Web 分组树 composable（confirm 取消不调 API）
 * 目录：tests/element-locator/p1/
 *
 * useWebGroupTree 无同级重名校验、无 maxDepth、无 bus 注册（见源码 onMounted/onUnmounted），
 * 主树其余 P1 点不适用于分组树，本文件只补 ElMessageBox.confirm 取消分支。
 * 统一 mock element-plus 与模块 api，不断真网络；wrapper 统一 afterEach unmount。
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, type VueWrapper } from '@vue/test-utils'
import { ElMessageBox } from 'element-plus'
import * as elApi from '@/modules/element-locator/api'
import { useWebGroupTree } from '@/modules/element-locator/composables/useWebGroupTree'
import { mountComposable } from '../../helpers/mountComposable'

vi.mock('element-plus', () => ({
  ElMessage: { success: vi.fn(), warning: vi.fn(), error: vi.fn(), info: vi.fn() },
  ElMessageBox: { confirm: vi.fn() },
}))
vi.mock('@/modules/element-locator/api', () => ({
  apiListWebGroups: vi.fn(),
  apiCreateWebGroup: vi.fn(),
  apiUpdateWebGroup: vi.fn(),
  apiDeleteWebGroup: vi.fn(),
  apiListWebElements: vi.fn(),
  apiBatchMoveWebGroups: vi.fn(),
}))

describe('[P1] element-locator useWebGroupTree', () => {
  const mounted: VueWrapper[] = []

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    mounted.forEach((w) => w.unmount())
    mounted.length = 0
  })

  it('deleteGroup：confirm 取消（reject）不调 apiDeleteWebGroup', async () => {
    vi.mocked(elApi.apiListWebGroups).mockResolvedValue({ data: { status: true, groups: [] } } as never)
    vi.mocked(ElMessageBox.confirm).mockRejectedValueOnce(new Error('cancel'))
    const { result, wrapper } = await mountComposable(() => useWebGroupTree())
    mounted.push(wrapper)
    await flushPromises()

    await result.deleteGroup({ id: 1, name: '分组A', is_folder: false })

    expect(ElMessageBox.confirm).toHaveBeenCalledTimes(1)
    expect(elApi.apiDeleteWebGroup).not.toHaveBeenCalled()
  })
})
