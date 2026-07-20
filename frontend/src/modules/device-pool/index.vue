<script setup>
/** Device Pool v2 — 设备管理主页面 per PRD-02 */
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from "vue";
import { animate, stagger } from "animejs";
import { ElMessage, ElMessageBox } from "element-plus";
// Card/Table/AppTabs → el-* (Element Plus auto-import)
import AppCard from "@/shared/components/AppCard.vue";
import AppTabs from "@/shared/components/AppTabs.vue";
import AppTable from "@/shared/components/AppTable.vue";
import { usePagination } from "@/shared/composables/usePagination.js";
import { IconWifi, IconRefresh } from "@/shared/icons/index.js";
import EmptyState from "@/shared/components/patterns/EmptyState.vue";
import { useDevicePoolStore } from "./store.js";
import DisconnectDialog from "./components/DisconnectDialog.vue";
import NetworkConnectDialog from "./components/NetworkConnectDialog.vue";
import QueuePanel from "./components/QueuePanel.vue";
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue";

const store = useDevicePoolStore();

// ── Local state ──
let heartbeatTimer = null;
let prevDevicesJson = "";

// JWT current user — from per-tab sessionStorage
function getCurrentUser() {
  const active = sessionStorage.getItem("auth_active") || ""
  if (active) return active
  // fallback: first from pool
  try {
    const pool = JSON.parse(localStorage.getItem("auth_accounts") || "{}")
    return Object.keys(pool)[0] || ""
  } catch { return "" }
}
const currentUser = getCurrentUser();

// Disconnect dialog
const disconnectDialog = ref({
  visible: false,
  serial: "",
  model: "",
  status: "",
  lockedBy: "",
  isBusyOthers: false,
});

// Network (LAN) connect dialog — PRD §3.7 F-07
const networkDialog = ref({ visible: false, loading: false });

// ── AppTabs filtering ──
const activeFilter = ref("all");
const filterAppTabs = [
  { key: "all", label: "全部设备" },
  { key: "online", label: "在线" },
  { key: "busy", label: "使用中" },
  { key: "offline", label: "离线" },
];

const filteredDevices = computed(() => {
  if (activeFilter.value === "all") return store.devices;
  if (activeFilter.value === "offline") return store.devices.filter(
    (d) => d.status === "OFFLINE" || d.status === "DISCONNECTED",
  );
  return store.devices.filter(
    (d) => d.status === activeFilter.value.toUpperCase(),
  );
});

// ── Pagination ──
const {
  PAGE_SIZE_OPTIONS, pageSize, currentPage, totalPages, pagedItems: pagedDevices, setPageSize, goPage
} = usePagination(filteredDevices, { options: [5, 10, 20] })

watch([activeFilter], () => { currentPage.value = 1 })
watch(filteredDevices, () => {
  if (currentPage.value > totalPages.value) currentPage.value = totalPages.value
})

// ── AppTable columns definition — minWidth 保证内容完整，溢出时横向滚动 ──
const columns = [
  { dataIndex: "serial", title: "序列号", minWidth: 200 },
  { dataIndex: "model", title: "型号", minWidth: 120 },
  { dataIndex: "screen", title: "分辨率", minWidth: 110, align: "center" },
  { dataIndex: "status", title: "状态", minWidth: 160, align: "center" },
  { dataIndex: "connection_type", title: "连接", minWidth: 90, align: "center" },
  { dataIndex: "lock_status", title: "锁定", minWidth: 100, align: "center" },
  { dataIndex: "last_seen", title: "最后在线", minWidth: 110 },
  { dataIndex: "actions", title: "操作", width: 220, fixed: "right" },
];

// ── Computed ──

// ── Lifecycle ──

onMounted(() => {
  loadDevices();
  startHeartbeat();
});
onUnmounted(() => {
  stopHeartbeat();
});

function startHeartbeat() {
  stopHeartbeat();
  heartbeatTimer = setInterval(loadDevices, 30000);
}
function stopHeartbeat() {
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer);
    heartbeatTimer = null;
  }
}

async function loadDevices() {
  await store.fetchDevices();
  await nextTick();
  const json = JSON.stringify(store.devices);
  if (json !== prevDevicesJson) {
    prevDevicesJson = json;
    animateDeviceRows();
  }
}

function animateDeviceRows() {
  animate(
    ".device-table-wrapper .el-table tbody tr, .device-table-wrapper table tbody tr",
    {
      opacity: [0, 1],
      translateY: [16, 0],
      delay: stagger(50),
      duration: 350,
      ease: "outCubic",
    },
  );
}

// ── Actions ──

async function handleRefresh() {
  // Merge scan + refresh: scan ADB first, then refresh the device list
  if (store.scanning || store.loading) return;
  const result = await store.doScan();
  if (result && result.ok) {
    ElMessage.success(`扫描完成，发现 ${result.count || 0} 台设备`);
  } else if (result && !result.ok) {
    ElMessage.error(result.error || "扫描失败");
  }
  await loadDevices();
}

// Network (LAN) connect flow — PRD §3.7 F-07
function openNetworkDialog() {
  networkDialog.value = { visible: true, loading: false };
}

async function handleNetworkConnect({ target }) {
  if (!target) return;
  networkDialog.value.loading = true;
  // store.doScan 内部已 try/catch，恒返回 { ok, error? }
  const result = await store.doScan(target);
  networkDialog.value.loading = false;
  if (result && result.ok) {
    ElMessage.success(`已连接 ${target}`);
    networkDialog.value.visible = false;
    // 单 target scan 只返回该设备，必须全量刷新以恢复完整列表
    await loadDevices();
  } else {
    // 失败：透传后端 error，弹窗保持打开可重试
    ElMessage.error((result && result.error) || "连接失败");
  }
}

function cancelNetworkDialog() {
  networkDialog.value.visible = false;
}

function handleRowClick(record) {
  if (!record || !record.serial) return;
  const dev = store.devices.find((d) => d.serial === record.serial);
  if (!dev) return;
  if (dev.status === "OFFLINE" || dev.status === "DISCONNECTED") return;
  store.selectDevice(record.serial);
}

// Lock toggle — JWT user direct lock/unlock (no dialog)
async function handleLockClick(device) {
  if (device.locked_by) {
    // Already locked → only the same user can unlock
    if (device.locked_by !== currentUser) {
      ElMessage.warning(`设备已被 ${device.locked_by} 锁定，只有锁定者可以解除`);
      return;
    }
    const result = await store.doRelease(device.serial, {
      unlock: true,
      reason: "manual",
      userId: currentUser,
    });
    if (result.ok) {
      ElMessage.success(`${device.serial} 已解除锁定`);
    } else {
      ElMessage.error(result.error || "操作失败");
    }
    return;
  }
  // Not locked → lock to current user
  if (!currentUser) {
    ElMessage.warning("无法获取当前用户信息，请重新登录");
    return;
  }
  const result = await store.doLock(device.serial, currentUser, 3600, "user");
  if (result.ok) {
    ElMessage.success(`已锁定 ${device.serial}`);
  } else {
    ElMessage.error(result.error || "锁定失败");
  }
}

// Occupy toggle — release only (occupation is done by runner/ai engine)
function handleOccupyClick(device) {
  if (device.occupied_by) {
    handleRelease(device.serial);
  }
}

// Release — process occupation
async function handleRelease(serial) {
  const dev = store.devices.find((d) => d.serial === serial);
  if (!dev) return;

  const occupiedBy = dev.occupied_by || "";
  const isRunnerOccupied =
    occupiedBy.startsWith("ai_agent") ||
    occupiedBy.startsWith("runner-") ||
    occupiedBy.startsWith("task-") ||
    occupiedBy.startsWith("run-");

  if (isRunnerOccupied) {
    ElMessage.error("设备正在执行用例，无法解除占用。请等待用例执行完毕。");
    return;
  }

  const result = await store.doRelease(serial, {
    userId: currentUser,
    reason: "manual",
  });
  if (result.ok) {
    ElMessage.success(`${serial} 已解除占用`);
  } else {
    ElMessage.error(result.error || "解除失败");
  }
}

// Disconnect flow
function openDisconnectDialog(serial) {
  const dev = store.devices.find((d) => d.serial === serial);
  if (!dev) return;
  const isBusyOthers =
    dev.status === "BUSY" && dev.locked_by && dev.locked_by !== currentUser;
  disconnectDialog.value = {
    visible: true,
    serial,
    model: dev.model || dev.name || "",
    status: dev.status,
    lockedBy: dev.locked_by || "",
    isBusyOthers,
  };
}

async function handleDisconnectConfirm({ reason }) {
  const { serial, isBusyOthers, lockedBy } = disconnectDialog.value;
  const result = await store.doDisconnect(serial, {
    force: isBusyOthers,
    reason,
    userId: currentUser,
    isAdmin: isBusyOthers,
  });
  if (result.ok) {
    ElMessage.success(`${serial} 已断开`);
    disconnectDialog.value.visible = false;
  } else {
    ElMessage.error(result.error || "断开失败");
  }
}

function cancelDisconnectDialog() {
  disconnectDialog.value.visible = false;
}

// Queue
async function handleCancelQueue(serial, uid) {
  await store.doLeaveQueue(serial, uid);
  await store.fetchQueue();
}

// ── Formatting ──

function statusTag(status) {
  const map = {
    ONLINE: { type: "success", text: "在线" },
    BUSY: { type: "warning", text: "使用中" },
    OFFLINE: { type: "info", text: "离线 · 不可用" },
    DISCONNECTED: { type: "danger", text: "已断开 · 不可用" },
  };
  return map[status] || { type: "info", text: status };
}

function isRowSelected(record) {
  return record && record.serial === store.selectedSerial;
}

function formatRelativeTime(iso) {
  if (!iso) return "—";
  const diff = Date.now() - new Date(iso).getTime();
  const sec = Math.floor(diff / 1000);
  if (sec < 60) return "刚刚";
  if (sec < 3600) return `${Math.floor(sec / 60)} 分钟前`;
  if (sec < 86400) return `${Math.floor(sec / 3600)} 小时前`;
  return new Date(iso).toLocaleDateString("zh-CN");
}

function displayModel(device) {
  const parts = [];
  if (device.brand) parts.push(device.brand);
  if (device.model) parts.push(device.model);
  return parts.length ? parts.join(" ") : "—";
}

function connectionLabel(type) {
  return type === "WIFI" ? "无线 ADB" : "USB 有线";
}
</script>

<template>
  <div class="doc-page wb-shell device-workbench">
    <WorkbenchHeader
      title="设备管理"
      subtitle="扫描、连接、锁定 Android 设备，管理设备状态与使用队列"
      mark="📱"
    >
      <template #actions>
        <QueuePanel
          :entries="store.queueEntries"
          :count="store.queueLength"
          @cancel="handleCancelQueue"
        />
      </template>
    </WorkbenchHeader>

    <div class="doc-body">
      <section class="doc-section device-section">
        <div class="doc-section__header">
          <h3 class="doc-section__title">
            设备列表
            <span class="doc-tag">Devices</span>
          </h3>
        </div>

        <!-- AppTabs 筛选 + 设备表格 -->
        <div class="filter-bar">
          <AppTabs
            class="device-tabs"
            :items="filterAppTabs"
            v-model="activeFilter"
            :leaf-animation="true"
            :shadow="true"
          >
            <template v-for="tab in filterAppTabs" #[tab.key] :key="tab.key">
              <div class="tab-panel">
                <div class="table-toolbar">
                  <div class="table-toolbar-left">
                    <div class="toolbar-actions">
                      <el-button class="wb-btn toolbar-icon-btn lan-btn" size="small" @click="openNetworkDialog">
                        <IconWifi :size="14" />
                        <span>局域网连接</span>
                      </el-button>
                      <el-button
                        class="wb-btn toolbar-icon-btn refresh-btn"
                        size="small"
                        :loading="store.scanning || store.loading"
                        @click="handleRefresh"
                      >
                        <IconRefresh :size="14" />
                        <span>刷新设备</span>
                      </el-button>
                    </div>
                    <div class="page-size-control">
                      <span class="toolbar-label">显示行数</span>
                      <div class="page-size-btns">
                        <button
                          v-for="n in PAGE_SIZE_OPTIONS"
                          :key="n"
                          type="button"
                          class="page-size-btn"
                          :class="{ active: pageSize === n }"
                          @click="setPageSize(n)"
                        >{{ n }}</button>
                      </div>
                    </div>
                  </div>
                  <div v-if="filteredDevices.length > 0" class="table-toolbar-right">
                    <span class="page-info">
                      第 {{ currentPage }} / {{ totalPages }} 页 · 共 {{ filteredDevices.length }} 台
                    </span>
                    <div v-if="totalPages > 1" class="page-nav">
                      <el-button class="wb-btn" size="small" :disabled="currentPage <= 1" @click="goPage(currentPage - 1)">上一页</el-button>
                      <el-button class="wb-btn" size="small" :disabled="currentPage >= totalPages" @click="goPage(currentPage + 1)">下一页</el-button>
                    </div>
                  </div>
                </div>
                <AppCard type="default" class="table-card">
                  <div class="device-table-wrapper">
                    <AppTable
                      :columns="columns"
                      :data-source="pagedDevices"
                    row-key="serial"
                    :striped="true"
                    :loading="store.loading"
                    empty-text="暂无设备，点击「刷新设备」扫描并连接设备"
                    @row-click="handleRowClick"
                  >
                    <!-- Serial number + selection dot -->
                    <template #cell-serial="{ record }">
                      <span v-if="isRowSelected(record)" class="row-dot"
                        >●</span
                      >
                      <span class="mono-text" :title="record.serial">{{
                        record.serial
                      }}</span>
                    </template>

                    <!-- Model: brand + model -->
                    <template #cell-model="{ record }">
                      <span>{{ displayModel(record) }}</span>
                    </template>

                    <!-- Screen resolution -->
                    <template #cell-screen="{ record }">
                      <span v-if="record.screen">{{ record.screen }}</span>
                      <span v-else class="text-muted">—</span>
                    </template>

                    <!-- Status: device state + user binding + process occupation -->
                    <template #cell-status="{ record }">
                      <div class="status-cell">
                        <el-tag
                          :type="statusTag(record.status).type"
                          size="small"
                          effect="dark"
                          round
                        >
                          {{ statusTag(record.status).text }}
                        </el-tag>
                        <!-- Execution engine occupation — highest priority -->
                        <el-tooltip
                          v-if="
                            record.occupied_by &&
                            record.status === 'BUSY' &&
                            ['runner-', 'ai_agent', 'task-', 'run-'].some((p) =>
                              record.occupied_by.startsWith(p),
                            )
                          "
                          :content="record.occupied_by"
                          placement="top"
                        >
                          <span class="occupied-badge executing-badge"
                            >执行中</span
                          >
                        </el-tooltip>
                        <!-- Other process occupation -->
                        <el-tooltip
                          v-else-if="record.occupied_by"
                          :content="record.occupied_by"
                          placement="top"
                        >
                          <span class="occupied-badge process-badge"
                            >占用中: {{ record.occupied_by }}</span
                          >
                        </el-tooltip>
                        <!-- User binding (no process occupation) -->
                        <span
                          v-else-if="record.locked_by"
                          class="occupied-badge locked-badge"
                          >已绑定: {{ record.locked_by }}</span
                        >
                      </div>
                    </template>

                    <!-- Connection type -->
                    <template #cell-connection_type="{ record }">
                      <span class="connection-text">{{
                        connectionLabel(record.connection_type)
                      }}</span>
                    </template>

                    <!-- Lock status -->
                    <template #cell-lock_status="{ record }">
                      <span
                        v-if="record.locked_by"
                        class="lock-badge lock-badge--locked"
                        :title="`锁定者: ${record.locked_by}`"
                      >{{ record.locked_by }}</span>
                      <span v-else class="lock-badge lock-badge--shared">共用</span>
                    </template>

                    <!-- Last seen -->
                    <template #cell-last_seen="{ record }">
                      <span class="last-seen-text">
                        {{ formatRelativeTime(record.last_seen) }}
                      </span>
                    </template>

                    <!-- Actions: user lock + process occupy -->
                    <template #cell-actions="{ record }">
                      <div class="action-btns">
                        <!-- Lock button: purple unlocked → red locked (auto-switch) -->
                        <el-button class="wb-btn lock-btn"
                          size="small"
                          type="primary"
                          :class="{ 'lock-btn--locked': record.locked_by }"
                          :danger="!!record.locked_by"
                          :plain="!record.locked_by"
                          :disabled="
                            record.status === 'OFFLINE' ||
                            record.status === 'DISCONNECTED' ||
                            (!!record.locked_by && record.locked_by !== currentUser)
                          "
                          @click="handleLockClick(record)"
                          >{{
                            record.locked_by
                              ? (record.locked_by === currentUser ? "解除锁定" : "已锁定")
                              : "锁定"
                          }}</el-button>
                        <!-- Occupy button: yellow, always labeled "解除占用" -->
                        <el-button class="wb-btn occupy-btn"
                          size="small"
                          type="primary"
                          :disabled="
                            record.status === 'OFFLINE' ||
                            record.status === 'DISCONNECTED' ||
                            !record.occupied_by
                          "
                          @click="handleOccupyClick(record)"
                          >解除占用</el-button>
                        <!-- Disconnect button: only for WIFI devices -->
                        <el-button
                          v-if="record.connection_type === 'WIFI'"
                          class="wb-btn disconnect-btn"
                          size="small"
                          type="danger"
                          plain
                          @click="openDisconnectDialog(record.serial)"
                          >断开</el-button>
                      </div>
                    </template>

                    <template #empty>
                      <EmptyState icon="📱"
                        :text="activeFilter === 'all' ? '暂无设备' : '没有匹配的设备'"
                        :hint="activeFilter === 'all' ? '点击「扫描设备」发现设备' : '尝试切换筛选条件'" />
                    </template>
                  </AppTable>
                  </div>
                </AppCard>
              </div>
            </template>
          </AppTabs>
          <span class="filter-count">{{ filteredDevices.length }} 台设备</span>
        </div>
      </section>
    </div>

    <!-- Dialogs -->
    <DisconnectDialog
      v-bind="disconnectDialog"
      @confirm="handleDisconnectConfirm"
      @cancel="cancelDisconnectDialog"
    />
    <NetworkConnectDialog
      :visible="networkDialog.visible"
      :loading="networkDialog.loading"
      @confirm="handleNetworkConnect"
      @cancel="cancelNetworkDialog"
    />
  </div>
</template>

<style scoped>
.device-workbench {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.doc-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.device-section {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 24px 28px 28px;
  gap: 18px;
}

.device-section .doc-section__header {
  flex-shrink: 0;
  padding-bottom: 2px;
}

/* ── Filter bar ── */
.filter-bar {
  flex: 1;
  min-height: 0;
  display: flex;
  align-items: stretch;
  justify-content: space-between;
  gap: 20px;
  padding: 0;
  overflow: hidden;
}
.device-tabs {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.device-tabs :deep(.el-tabs) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.device-tabs :deep(.el-tabs__list) {
  flex-shrink: 0;
}
.device-tabs :deep(.el-tabs__content) {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding-top: 22px;
}
.device-tabs :deep(.el-tabs__header) {
  margin-bottom: 0;
}
.device-tabs :deep(.el-tabs__inner) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.tab-panel {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.filter-count {
  font-size: 13px;
  color: var(--app-text-secondary);
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
  padding-top: 14px;
  align-self: flex-start;
}

/* ── AppTable toolbar ── */
.table-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  flex-wrap: wrap;
  padding: 0 0 14px;
  flex-shrink: 0;
}
.table-toolbar-left { display: flex; align-items: center; gap: 20px; flex-wrap: wrap; }
.toolbar-actions { display: flex; align-items: center; gap: 10px; }

/* ── Toolbar icon buttons — AnimalButton root gets parent classes merged ── */
.toolbar-icon-btn {
  gap: 5px !important;
  padding: 5px 14px !important;
  border-radius: var(--app-radius-pill) !important;
}

.lan-btn {
  background: rgba(162,210,255,0.16) !important;
  border-color: rgba(162,210,255,0.38) !important;
  color: var(--app-green-deep) !important;
}
.lan-btn:hover {
  background: rgba(162,210,255,0.26) !important;
  border-color: rgba(162,210,255,0.62) !important;
}

.refresh-btn {
  background: rgba(111,185,141,0.14) !important;
  border-color: rgba(111,185,141,0.34) !important;
  color: #4c9a69 !important;
}
.refresh-btn:hover {
  background: rgba(111,185,141,0.24) !important;
  border-color: rgba(111,185,141,0.58) !important;
}
.page-size-control { display: flex; align-items: center; gap: 10px; }
.toolbar-label { font-size: 12px; font-weight: 700; color: var(--app-text-secondary); white-space: nowrap; }
.page-size-btns { display: flex; gap: 6px; }
.page-size-btn {
  min-width: 40px;
  padding: 5px 10px;
  border-radius: var(--app-radius-pill);
  border: 1.5px solid var(--app-glass-border);
  background: var(--app-glass-card);
  color: var(--app-text-secondary);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: var(--app-shadow-sm);
  transition: all var(--app-duration) var(--app-ease);
}
.page-size-btn:hover { border-color: var(--app-blue); color: var(--app-green-deep); }
.page-size-btn.active {
  background: rgba(162,210,255,0.20);
  border-color: rgba(162,210,255,0.62);
  color: var(--app-green-deep);
}
.table-toolbar-right { display: flex; align-items: center; gap: 12px; margin-left: auto; flex-wrap: wrap; }
.page-info { font-size: 12px; color: var(--app-text-secondary); font-weight: 600; white-space: nowrap; }
.page-nav { display: flex; gap: 8px; }

/* ── AppTable card ── */
.table-card {
  flex: 1;
  min-height: 0;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.table-card :deep(.el-card__body) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0;
  border-radius: var(--app-radius-lg);
  background: rgba(255,255,255,0.38);
  backdrop-filter: blur(var(--app-glass-blur));
  -webkit-backdrop-filter: blur(var(--app-glass-blur));
}

/* ── AppTable wrapper inside AppCard ── */
.device-table-wrapper {
  flex: 1;
  min-height: 0;
  min-width: 0;
  padding: 0;
  overflow-y: auto;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: thin;
  scrollbar-color: rgba(162,210,255,0.55) transparent;
}
.device-table-wrapper::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
.device-table-wrapper::-webkit-scrollbar-thumb {
  background: rgba(162,210,255,0.55);
  border-radius: 3px;
}
.device-table-wrapper :deep(.el-table),
.device-table-wrapper :deep(.el-table__body-wrapper) {
  overflow: visible !important;
  max-height: none !important;
}

/* ── 表头与正文颜色区分 + 行列线条 ── */
.device-table-wrapper :deep(.el-table th) {
  background: rgba(162,210,255,0.13) !important;
  color: var(--app-text-muted, #a8b5c4) !important;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.4px;
  border-right: 1px solid rgba(162,210,255,0.22) !important;
  border-bottom: 2px solid rgba(162,210,255,0.30) !important;
}
.device-table-wrapper :deep(.el-table td) {
  color: var(--app-text, #4a4e69);
  font-size: 13px;
  border-right: 1px solid rgba(162,210,255,0.12) !important;
  border-bottom: 1px solid rgba(162,210,255,0.10) !important;
}
.device-table-wrapper :deep(.el-table th:last-child),
.device-table-wrapper :deep(.el-table td:last-child) {
  border-right: none !important;
}

/* ── 操作列垂直居中 ── */
.device-table-wrapper :deep(.el-table td:last-child) {
  vertical-align: middle;
}

/* ── Row dot indicator ── */
.row-dot {
  color: var(--accent-blue, #409eff);
  font-size: 12px;
  line-height: 1;
  margin-right: 6px;
  vertical-align: middle;
}

/* ── Status + occupancy badge ── */
.status-cell {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  justify-content: center;
}
.occupied-badge {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 8px;
  font-weight: 600;
  max-width: 130px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.executing-badge {
  background: rgba(232,153,138,0.16);
  color: var(--ac-red);
  border: 1px solid rgba(232,153,138,0.30);
}
.process-badge {
  background: rgba(255,214,165,0.26);
  color: #9a6a1f;
  border: 1px solid rgba(255,214,165,0.48);
}
.locked-badge {
  background: rgba(162,210,255,0.18);
  color: var(--app-green-deep);
  border: 1px solid rgba(162,210,255,0.42);
}

/* ── Monospace serial text ── */
.mono-text {
  font-family: "Cascadia Code", "Fira Code", "Consolas", monospace;
  font-size: 13px;
  white-space: nowrap;
  vertical-align: middle;
}

/* ── Text helpers ── */
.text-muted {
  color: var(--app-text-muted);
  font-size: 13px;
}

.locked-by-text {
  color: var(--text-secondary, #909399);
  font-size: 13px;
}

.last-seen-text {
  font-size: 13px;
  color: var(--text-secondary, #909399);
}

.connection-text {
  font-size: 13px;
  color: var(--app-text);
  font-weight: 600;
  white-space: nowrap;
}

/* ── Action buttons row ── */
.action-btns {
  display: flex;
  flex-direction: column;
  gap: 3px;
  align-items: stretch;
}
.action-btns .wb-btn {
  width: 100%;
  min-width: 0;
  font-size: 11px;
  padding: 3px 10px;
}

/* ── Action button colors ── */
/* Lock: purple (unlocked) → red (locked, via danger prop) */
.lock-btn:not(.lock-btn--locked) {
  background: rgba(200,182,255,0.20) !important;
  border-color: rgba(200,182,255,0.46) !important;
  color: #7059bd !important;
}
.lock-btn:not(.lock-btn--locked):hover {
  background: rgba(200,182,255,0.32) !important;
  border-color: rgba(200,182,255,0.68) !important;
}
.occupy-btn {
  background: rgba(255,214,165,0.24) !important;
  border-color: rgba(255,214,165,0.52) !important;
  color: #9a6a1f !important;
}
.occupy-btn:hover:not(.is-disabled) {
  background: rgba(255,214,165,0.36) !important;
  border-color: rgba(255,214,165,0.72) !important;
}
.disconnect-btn {
  background: rgba(232,95,95,0.10) !important;
  border-color: rgba(232,95,95,0.32) !important;
  color: #d45656 !important;
}
.disconnect-btn:hover:not(.is-disabled) {
  background: rgba(232,95,95,0.20) !important;
  border-color: rgba(232,95,95,0.52) !important;
}

/* ── Lock status badge ── */
.lock-badge {
  font-size: 11px;
  padding: 2px 10px;
  border-radius: 10px;
  font-weight: 700;
  white-space: nowrap;
  display: inline-block;
}
.lock-badge--locked {
  background: rgba(162,210,255,0.18);
  color: var(--app-green-deep);
  border: 1px solid rgba(162,210,255,0.42);
}
.lock-badge--shared {
  background: rgba(111,185,141,0.16);
  color: #4c9a69;
  border: 1px solid rgba(111,185,141,0.36);
}

/* ── Empty state ── */
.empty-state {
  color: var(--app-text-secondary);
  padding: 40px 0;
  text-align: center;
  font-size: 14px;
}

/* ── Row status styles (deep targeting animal-island table rows) ── */
:deep(.device-table-wrapper .el-table tbody tr[data-row-status="OFFLINE"]),
:deep(
  .device-table-wrapper .el-table tbody tr[data-row-status="DISCONNECTED"]
) {
  opacity: 0.5;
}
</style>
