<script setup>
/** Device Pool v2 — 设备管理主页面 per PRD §7 (animal-island-vue redesign) */
import { ref, computed, onMounted, onUnmounted, nextTick } from "vue";
import { useRouter } from "vue-router";
import { animate, stagger } from "animejs";
import { ElMessage, ElMessageBox } from "element-plus";
import { Button as AnimalButton, Card, Table, Tabs } from "animal-island-vue";
import { useDevicePoolStore } from "./store.js";
import LockDialog from "./components/LockDialog.vue";
import DisconnectDialog from "./components/DisconnectDialog.vue";
import NetworkConnectDialog from "./components/NetworkConnectDialog.vue";
import QueuePanel from "./components/QueuePanel.vue";
import PageHeader from "@/shared/components/PageHeader.vue";

const router = useRouter();
const store = useDevicePoolStore();

// ── Local state ──
let heartbeatTimer = null;
let prevDevicesJson = "";

// Lock dialog
const lockDialog = ref({ visible: false, serial: "", model: "" });

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

// ── Tabs filtering ──
const activeFilter = ref("all");
const filterTabs = [
  { key: "all", label: "在线设备" },
  { key: "busy", label: "使用中" },
];

// 全局过滤掉离线设备
const onlineDevices = computed(() =>
  store.devices.filter(
    (d) => d.status !== "OFFLINE" && d.status !== "DISCONNECTED",
  ),
);

const filteredDevices = computed(() => {
  if (activeFilter.value === "all") return onlineDevices.value;
  if (activeFilter.value === "offline") return [];
  return onlineDevices.value.filter(
    (d) => d.status === activeFilter.value.toUpperCase(),
  );
});

// ── Table columns definition (animal-island Table API) ──
const columns = [
  { dataIndex: "serial", title: "序列号", width: 220 },
  { dataIndex: "model", title: "型号", width: 180 },
  { dataIndex: "screen", title: "分辨率", width: 130, align: "center" },
  { dataIndex: "status", title: "状态", width: 100, align: "center" },
  { dataIndex: "connection_type", title: "连接", width: 88, align: "center" },
  { dataIndex: "last_seen", title: "最后在线", width: 120 },
  { dataIndex: "actions", title: "操作", width: 360, fixed: "right" },
];

// ── Computed ──

const userId = ref(localStorage.getItem("dp_user_id") || "");
function saveUserId(id) {
  userId.value = id;
  localStorage.setItem("dp_user_id", id);
}

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
    ".device-table-wrapper .animal-table tbody tr, .device-table-wrapper table tbody tr",
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

async function handleConnect(serial) {
  if (!serial) return;
  const dev = store.devices.find((d) => d.serial === serial);
  if (!dev) return;

  if (dev.status === "OFFLINE" || dev.status === "DISCONNECTED") {
    ElMessage.warning("设备已离线，请重新扫描");
    return;
  }
  if (dev.status === "BUSY" && dev.occupied_by) {
    ElMessage.warning(`设备正被 ${dev.occupied_by} 占用中`);
    return;
  }
  if (dev.locked_by && dev.locked_by !== userId.value) {
    ElMessage.warning(`设备已被 ${dev.locked_by} 绑定`);
    return;
  }

  const result = await store.doConnect(serial, {
    activate: true,
    userId: userId.value,
  });
  if (result.ok) {
    ElMessage.success(`已连接 ${result.model || serial}`);
    router.push({ path: "/elements", query: { serial, autoStart: "1" } });
  } else {
    ElMessage.error(result.error || "连接失败");
  }
}

// Lock flow
function openLockDialog(serial) {
  const dev = store.devices.find((d) => d.serial === serial);
  lockDialog.value = {
    visible: true,
    serial,
    model: dev ? `${dev.brand} ${dev.model}`.trim() : "",
  };
}

async function handleLockConfirm({ userId: uid, timeout }) {
  const serial = lockDialog.value.serial;
  saveUserId(uid);
  const result = await store.doLock(serial, uid, timeout);
  if (result.ok) {
    ElMessage.success(`已锁定 ${serial}`);
    lockDialog.value.visible = false;
  } else if (result.remaining !== undefined) {
    ElMessage.warning(
      result.error ||
        `设备已被 ${result.locked_by} 锁定，剩余 ${result.remaining} 秒`,
    );
    lockDialog.value.visible = false;
  } else {
    ElMessage.error(result.error || "锁定失败");
  }
}

function cancelLockDialog() {
  lockDialog.value.visible = false;
}

// Lock toggle — user binding
async function handleLockClick(device) {
  if (device.locked_by) {
    // Already locked → unlock (clear user binding)
    if (device.occupied_by) {
      const confirmed = await new Promise((resolve) => {
        ElMessageBox.confirm(
          `设备当前被「${device.occupied_by}」占用中，确定要解除用户绑定吗？`,
          "确认解除锁定",
          {
            confirmButtonText: "确定解除",
            cancelButtonText: "取消",
            type: "warning",
          },
        )
          .then(() => resolve(true))
          .catch(() => resolve(false));
      });
      if (!confirmed) return;
    }
    const result = await store.doRelease(device.serial, {
      unlock: true,
      reason: "manual",
    });
    if (result.ok) {
      ElMessage.success(`${device.serial} 已解除锁定`);
    } else {
      ElMessage.error(result.error || "操作失败");
    }
    return;
  }
  if (device.occupied_by) {
    ElMessage.warning(`设备正被 ${device.occupied_by} 占用中，仍可绑定用户`);
  }
  openLockDialog(device.serial);
}

// Occupy toggle — process occupation
function handleOccupyClick(device) {
  if (device.occupied_by) {
    handleRelease(device.serial);
    return;
  }
  // Occupy: prompt for process name, then call lock with that process ID
  ElMessageBox.prompt("请输入占用此设备的进程名称", "占用设备", {
    confirmButtonText: "确认占用",
    cancelButtonText: "取消",
    inputValue: "runner-task-" + Date.now().toString(36),
    inputPlaceholder: "如：runner-task-001、ai_agent",
  })
    .then(({ value }) => {
      if (value && value.trim()) {
        store
          .doLock(device.serial, value.trim(), 3600, "occupy")
          .then((result) => {
            if (result.ok) {
              ElMessage.success(`${device.serial} 已被 ${value.trim()} 占用`);
            } else {
              ElMessage.error(result.error || "占用失败");
            }
          });
      }
    })
    .catch(() => {});
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
    userId: userId.value,
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
    dev.status === "BUSY" && dev.locked_by && dev.locked_by !== userId.value;
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
    userId: userId.value,
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
    OFFLINE: { type: "info", text: "离线" },
    DISCONNECTED: { type: "danger", text: "已断开" },
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
  <div class="doc-page dp-animal-theme">
    <PageHeader
      title="设备管理 Device Pool"
      subtitle="扫描、连接、锁定 Android / iOS 设备，管理设备状态与使用队列"
      color="app-yellow"
    />

    <div class="doc-body">
      <section class="doc-section device-section">
        <div class="doc-section__header">
          <h3 class="doc-section__title">
            设备列表
            <span class="doc-tag">Devices</span>
          </h3>
          <div class="header-actions">
            <QueuePanel
              :entries="store.queueEntries"
              :count="store.queueLength"
              @cancel="handleCancelQueue"
            />
            <AnimalButton type="primary" @click="openNetworkDialog">
              局域网连接
            </AnimalButton>
            <AnimalButton
              type="primary"
              @click="handleRefresh"
              :loading="store.scanning || store.loading"
            >
              刷新设备
            </AnimalButton>
          </div>
        </div>

        <!-- Tabs 筛选 + 设备表格 -->
        <div class="filter-bar">
          <Tabs
            class="device-tabs"
            :items="filterTabs"
            v-model="activeFilter"
            :leaf-animation="true"
            :shadow="true"
          >
            <template v-for="tab in filterTabs" #[tab.key] :key="tab.key">
              <Card color="app-yellow" pattern="app-yellow" type="default">
                <div class="device-table-wrapper">
                  <Table
                    :columns="columns"
                    :data-source="filteredDevices"
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

                    <!-- Last seen -->
                    <template #cell-last_seen="{ record }">
                      <span class="last-seen-text">
                        {{ formatRelativeTime(record.last_seen) }}
                      </span>
                    </template>

                    <!-- Two independent pairs: user lock + process occupy -->
                    <template #cell-actions="{ record }">
                      <div class="action-btns">
                        <AnimalButton
                          size="small"
                          type="primary"
                          plain
                          :disabled="
                            record.status === 'OFFLINE' ||
                            record.status === 'DISCONNECTED'
                          "
                          @click="handleLockClick(record)"
                          >{{
                            record.locked_by ? "解除锁定" : "锁定用户"
                          }}</AnimalButton
                        >
                        <AnimalButton
                          size="small"
                          :type="record.occupied_by ? 'danger' : 'warning'"
                          plain
                          :disabled="
                            record.status === 'OFFLINE' ||
                            record.status === 'DISCONNECTED'
                          "
                          @click="handleOccupyClick(record)"
                          >{{
                            record.occupied_by ? "解除占用" : "占用设备"
                          }}</AnimalButton
                        >
                      </div>
                    </template>

                    <!-- Empty state -->
                    <template #empty>
                      <div class="empty-state">
                        <span v-if="activeFilter === 'all'"
                          >暂无设备，点击「扫描设备」发现设备</span
                        >
                        <span v-else>当前筛选条件下没有设备</span>
                      </div>
                    </template>
                  </Table>
                </div>
              </Card>

              <div class="bottom-bar">
                <AnimalButton
                  type="primary"
                  :disabled="!store.selectedSerial"
                  @click="handleConnect(store.selectedSerial)"
                >
                  连接选中设备
                </AnimalButton>
                <span v-if="!store.selectedSerial" class="bottom-hint">
                  请先点击设备行选中一台设备
                </span>
                <span v-else class="bottom-hint selected-hint">
                  已选择：{{ store.selectedSerial }}
                </span>
              </div>
            </template>
          </Tabs>
          <span class="filter-count">{{ filteredDevices.length }} 台设备</span>
        </div>
      </section>
    </div>

    <!-- Dialogs -->
    <LockDialog
      v-bind="lockDialog"
      @confirm="handleLockConfirm"
      @cancel="cancelLockDialog"
    />
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
.dp-animal-theme {
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
  padding: 20px 24px 24px;
}

.device-section .doc-section__header {
  flex-shrink: 0;
}

/* ── Filter bar ── */
.filter-bar {
  flex: 1;
  min-height: 0;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 0 4px;
}
.device-tabs {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.device-tabs :deep(.animal-tabs) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.device-tabs :deep(.animal-tabs__content) {
  flex: 1;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
  display: block;
  padding-top: 16px;
}
.device-tabs :deep(.animal-tabs__inner) {
  min-height: min-content;
}
.filter-count {
  font-size: 13px;
  color: #9f927d;
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
  padding-top: 10px;
}

/* ── Table wrapper inside Card ── */
.device-table-wrapper {
  padding: 0;
}
.device-table-wrapper :deep(.animal-card__content) {
  padding: 0;
  border-radius: 16px;
  background: rgba(255, 248, 240, 0.85);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
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
  align-items: center;
  gap: 6px;
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
  background: #fde8e8;
  color: #e85f5f;
}
.process-badge {
  background: #fef3cd;
  color: #8a6d14;
}
.locked-badge {
  background: #e8f0fe;
  color: #5a7d9a;
}

/* ── Monospace serial text ── */
.mono-text {
  font-family: "Cascadia Code", "Fira Code", "Consolas", monospace;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 180px;
  display: inline-block;
  vertical-align: middle;
}

/* ── Text helpers ── */
.text-muted {
  color: #ccc;
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
  color: #725d42;
  font-weight: 600;
  white-space: nowrap;
}

/* ── Action buttons row ── */
.action-btns {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

/* ── Bottom bar ── */
.bottom-bar {
  display: flex;
  align-items: center;
  padding: 16px 0 0;
  margin-top: 16px;
  border-top: 1px solid var(--el-border-color-lighter, #ebeef5);
}
.bottom-hint {
  margin-left: 12px;
  color: var(--text-secondary, #909399);
  font-size: 13px;
}
.selected-hint {
  color: var(--accent-blue, #409eff);
  font-weight: 600;
  font-family: "Cascadia Code", "Fira Code", "Consolas", monospace;
}

/* ── Empty state ── */
.empty-state {
  color: #9f927d;
  padding: 40px 0;
  text-align: center;
  font-size: 14px;
}

/* ── Row status styles (deep targeting animal-island table rows) ── */
:deep(.device-table-wrapper .animal-table tbody tr[data-row-status="OFFLINE"]),
:deep(
  .device-table-wrapper .animal-table tbody tr[data-row-status="DISCONNECTED"]
) {
  opacity: 0.5;
}
</style>
