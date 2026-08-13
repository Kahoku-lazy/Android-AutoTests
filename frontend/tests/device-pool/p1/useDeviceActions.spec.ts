/**
 * [P1] 建议测 — 设备操作消息分支与断开弹窗标志（池对象桩注入，不 mock api）
 * 目录：tests/device-pool/p1/
 *
 * useDeviceActions：各 handler 成功/失败 ElMessage 文案、openDisconnectDialog 的 isBusyOthers 计算。
 */
import { ref } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ElMessage } from 'element-plus'
import {
  useDeviceActions,
  type UseDeviceActionsReturn,
} from '@/modules/device-pool/composables/useDeviceActions'
import type { UseDevicePoolStateReturn } from '@/modules/device-pool/composables/useDevicePoolState'
import type { DeviceRecord } from '@/shared/types/device'

vi.mock('element-plus', () => ({
  ElMessage: { success: vi.fn(), warning: vi.fn(), error: vi.fn() },
}))
vi.mock('animejs', () => ({ animate: vi.fn(), stagger: vi.fn() }))
vi.mock('@/shared/auth/token-storage', () => ({
  getActive: vi.fn(() => 'u1'),
  getActiveUsername: vi.fn(() => 'u1'),
}))

function makeDevice(serial: string, extra: Partial<DeviceRecord> = {}): DeviceRecord {
  return {
    serial,
    model: 'Pixel 6',
    status: 'ONLINE',
    connection_type: 'USB',
    last_seen: '2026-08-13 10:00',
    ...extra,
  }
}

function makePool(overrides: Partial<UseDevicePoolStateReturn> = {}): UseDevicePoolStateReturn {
  return {
    devices: ref<DeviceRecord[]>([]),
    scanning: ref(false),
    loading: ref(false),
    fetchDevices: vi.fn().mockResolvedValue(undefined),
    doScan: vi.fn().mockResolvedValue({ status: false, message: '扫描失败' }),
    doLock: vi.fn().mockResolvedValue({ status: true }),
    doRelease: vi.fn().mockResolvedValue({ status: true }),
    doJoinQueue: vi.fn().mockResolvedValue({ status: true }),
    doLeaveQueue: vi.fn().mockResolvedValue({ status: true }),
    doDisconnect: vi.fn().mockResolvedValue({ status: true }),
    fetchQueue: vi.fn().mockResolvedValue(undefined),
    selectDevice: vi.fn(),
    ...overrides,
  } as unknown as UseDevicePoolStateReturn
}

type BranchRow = {
  name: string
  devices?: DeviceRecord[]
  arrange: (p: UseDevicePoolStateReturn) => void
  act: (a: UseDeviceActionsReturn) => Promise<void>
  expectMsg: string
  extra?: (a: UseDeviceActionsReturn) => void
}

const successRows: BranchRow[] = [
  {
    name: 'handleRefresh 成功：扫描完成文案',
    arrange: (p) => vi.mocked(p.doScan).mockResolvedValue({ status: true, count: 3 }),
    act: (a) => a.handleRefresh(),
    expectMsg: '扫描完成，发现 3 台设备',
  },
  {
    name: 'handleNetworkConnect 成功：已连接文案并关闭弹窗',
    arrange: (p) => vi.mocked(p.doScan).mockResolvedValue({ status: true }),
    act: async (a) => {
      a.openNetworkDialog()
      await a.handleNetworkConnect({ target: '192.168.1.10' })
    },
    expectMsg: '已连接 192.168.1.10',
    extra: (a) => expect(a.networkDialog.value.visible).toBe(false),
  },
  {
    name: 'handleLockClick 本人锁：解除成功文案',
    arrange: (p) => vi.mocked(p.doRelease).mockResolvedValue({ status: true }),
    act: (a) => a.handleLockClick(makeDevice('S1', { locked_by: 'u1' })),
    expectMsg: 'S1 已解除锁定',
  },
  {
    name: 'handleLockClick 无锁设备：锁定成功文案',
    arrange: (p) => vi.mocked(p.doLock).mockResolvedValue({ status: true }),
    act: (a) => a.handleLockClick(makeDevice('S1')),
    expectMsg: '已锁定 S1',
  },
  {
    name: 'handleJoinQueue 成功：含排位文案',
    arrange: (p) => vi.mocked(p.doJoinQueue).mockResolvedValue({ status: true, position: 2 }),
    act: (a) => a.handleJoinQueue(makeDevice('S1')),
    expectMsg: '已加入 S1 的等待队列，当前位置：第 2 位',
  },
  {
    name: 'handleRelease 成功：已解除占用文案',
    devices: [makeDevice('S1', { occupied_by: 'u2' })],
    arrange: (p) => vi.mocked(p.doRelease).mockResolvedValue({ status: true }),
    act: (a) => a.handleRelease('S1'),
    expectMsg: 'S1 已解除占用',
  },
  {
    name: 'handleDisconnectConfirm 成功：已断开文案并关闭弹窗',
    arrange: (p) => vi.mocked(p.doDisconnect).mockResolvedValue({ status: true }),
    act: async (a) => {
      a.disconnectDialog.value = { ...a.disconnectDialog.value, visible: true, serial: 'S1' }
      await a.handleDisconnectConfirm({ reason: '手滑' })
    },
    expectMsg: 'S1 已断开',
    extra: (a) => expect(a.disconnectDialog.value.visible).toBe(false),
  },
]

const failureRows: BranchRow[] = [
  {
    name: 'handleRefresh 失败：扫描失败文案',
    arrange: (p) => vi.mocked(p.doScan).mockResolvedValue({ status: false, message: '扫描失败' }),
    act: (a) => a.handleRefresh(),
    expectMsg: '扫描失败',
  },
  {
    name: 'handleNetworkConnect 失败：连接失败文案且弹窗不关闭',
    arrange: (p) => vi.mocked(p.doScan).mockResolvedValue({ status: false, message: '连接失败' }),
    act: async (a) => {
      a.openNetworkDialog()
      await a.handleNetworkConnect({ target: '192.168.1.10' })
    },
    expectMsg: '连接失败',
    extra: (a) => expect(a.networkDialog.value.visible).toBe(true),
  },
  {
    name: 'handleLockClick 解除失败：操作失败文案',
    arrange: (p) => vi.mocked(p.doRelease).mockResolvedValue({ status: false, message: '操作失败' }),
    act: (a) => a.handleLockClick(makeDevice('S1', { locked_by: 'u1' })),
    expectMsg: '操作失败',
  },
  {
    name: 'handleLockClick 锁定失败：锁定失败文案',
    arrange: (p) => vi.mocked(p.doLock).mockResolvedValue({ status: false, message: '锁定失败' }),
    act: (a) => a.handleLockClick(makeDevice('S1')),
    expectMsg: '锁定失败',
  },
  {
    name: 'handleJoinQueue 失败：加入队列失败文案',
    arrange: (p) =>
      vi.mocked(p.doJoinQueue).mockResolvedValue({ status: false, message: '加入队列失败' }),
    act: (a) => a.handleJoinQueue(makeDevice('S1')),
    expectMsg: '加入队列失败',
  },
  {
    name: 'handleRelease 失败：解除失败文案',
    devices: [makeDevice('S1', { occupied_by: '' })],
    arrange: (p) => vi.mocked(p.doRelease).mockResolvedValue({ status: false, message: '解除失败' }),
    act: (a) => a.handleRelease('S1'),
    expectMsg: '解除失败',
  },
  {
    name: 'handleDisconnectConfirm 失败：断开失败文案',
    arrange: (p) => vi.mocked(p.doDisconnect).mockResolvedValue({ status: false, message: '断开失败' }),
    act: async (a) => {
      a.disconnectDialog.value = { ...a.disconnectDialog.value, visible: true, serial: 'S1' }
      await a.handleDisconnectConfirm({ reason: '手滑' })
    },
    expectMsg: '断开失败',
  },
]

describe('[P1] useDeviceActions', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it.each(successRows)('$name', async (row) => {
    const pool = makePool({ devices: ref(row.devices ?? []) })
    row.arrange(pool)
    const actions = useDeviceActions(pool)

    await row.act(actions)

    expect(vi.mocked(ElMessage.success)).toHaveBeenCalledWith(row.expectMsg)
    expect(vi.mocked(ElMessage.error)).not.toHaveBeenCalled()
    row.extra?.(actions)
  })

  it.each(failureRows)('$name', async (row) => {
    const pool = makePool({ devices: ref(row.devices ?? []) })
    row.arrange(pool)
    const actions = useDeviceActions(pool)

    await row.act(actions)

    expect(vi.mocked(ElMessage.error)).toHaveBeenCalledWith(row.expectMsg)
    expect(vi.mocked(ElMessage.success)).not.toHaveBeenCalled()
    row.extra?.(actions)
  })

  describe('openDisconnectDialog isBusyOthers', () => {
    it('他人占用：isBusyOthers=true，弹窗记录锁定者', () => {
      const pool = makePool({
        devices: ref([makeDevice('S1', { status: 'BUSY', locked_by: 'other-user' })]),
      })
      const actions = useDeviceActions(pool)

      actions.openDisconnectDialog('S1')

      expect(actions.disconnectDialog.value).toEqual({
        visible: true,
        serial: 'S1',
        model: 'Pixel 6',
        status: 'BUSY',
        lockedBy: 'other-user',
        isBusyOthers: true,
      })
    })

    it('本人锁定：isBusyOthers=false', () => {
      const pool = makePool({
        devices: ref([makeDevice('S1', { status: 'BUSY', locked_by: 'u1' })]),
      })
      const actions = useDeviceActions(pool)

      actions.openDisconnectDialog('S1')

      expect(actions.disconnectDialog.value.isBusyOthers).toBe(false)
      expect(actions.disconnectDialog.value.lockedBy).toBe('u1')
    })

    it('非 BUSY 状态：isBusyOthers=false', () => {
      const pool = makePool({
        devices: ref([makeDevice('S1', { status: 'ONLINE', locked_by: 'other-user' })]),
      })
      const actions = useDeviceActions(pool)

      actions.openDisconnectDialog('S1')

      expect(actions.disconnectDialog.value.isBusyOthers).toBe(false)
    })
  })
})
