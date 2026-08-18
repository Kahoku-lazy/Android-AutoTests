/**
 * [P1] 建议测 — 设备操作消息分支（池对象桩注入，不 mock api）
 * 目录：tests/device-pool/p1/
 *
 * useDeviceActions：各 handler 成功/失败 ElMessage 文案、锁定/公开切换、释放、删除。
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
    doDisconnect: vi.fn().mockResolvedValue({ status: true }),
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
    arrange: (p) => vi.mocked(p.doScan).mockResolvedValue({ status: true, data: { count: 3 } }),
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
    name: 'handleLockClick 公开设备：锁定成功文案',
    arrange: (p) => vi.mocked(p.doLock).mockResolvedValue({ status: true }),
    act: (a) => a.handleLockClick(makeDevice('S1', { locked: false })),
    expectMsg: '已锁定 S1',
  },
  {
    name: 'handleLockClick 已锁定设备：公开成功文案',
    arrange: (p) => vi.mocked(p.doLock).mockResolvedValue({ status: true }),
    act: (a) => a.handleLockClick(makeDevice('S1', { locked: true })),
    expectMsg: 'S1 已公开',
  },
  {
    name: 'handleRelease 成功：已解除占用文案',
    arrange: (p) => vi.mocked(p.doRelease).mockResolvedValue({ status: true }),
    act: (a) => a.handleRelease('S1'),
    expectMsg: 'S1 已解除占用',
  },
  {
    name: 'handleDisconnectConfirm 成功：已删除文案并关闭弹窗',
    arrange: (p) => vi.mocked(p.doDisconnect).mockResolvedValue({ status: true }),
    act: async (a) => {
      a.disconnectDialog.value = { ...a.disconnectDialog.value, visible: true, serial: 'S1' }
      await a.handleDisconnectConfirm()
    },
    expectMsg: 'S1 已删除',
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
    name: 'handleLockClick 失败：操作失败文案',
    arrange: (p) => vi.mocked(p.doLock).mockResolvedValue({ status: false, message: '操作失败' }),
    act: (a) => a.handleLockClick(makeDevice('S1', { locked: false })),
    expectMsg: '操作失败',
  },
  {
    name: 'handleRelease 失败：释放失败文案',
    arrange: (p) => vi.mocked(p.doRelease).mockResolvedValue({ status: false, message: '释放失败' }),
    act: (a) => a.handleRelease('S1'),
    expectMsg: '释放失败',
  },
  {
    name: 'handleDisconnectConfirm 失败：删除失败文案',
    arrange: (p) => vi.mocked(p.doDisconnect).mockResolvedValue({ status: false, message: '删除失败' }),
    act: async (a) => {
      a.disconnectDialog.value = { ...a.disconnectDialog.value, visible: true, serial: 'S1' }
      await a.handleDisconnectConfirm()
    },
    expectMsg: '删除失败',
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
})
