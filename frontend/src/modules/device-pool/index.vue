<script setup>
/** Device Pool v2 — 设备管理主页面 per PRD-02 */
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from "vue";
import { animate, stagger } from "animejs";
import { ElMessage, ElMessageBox } from "element-plus";
// Card/Table/AppTabs → el-* (Element Plus auto-import)
import AppTable from "@/shared/components/AppTable.vue";
import DeviceFilterTabs from "./components/DeviceFilterTabs.vue";
import DeviceCard from "./components/DeviceCard.vue";
import DeviceStatusCell from "./components/DeviceStatusCell.vue";
import DeviceActionsCell from "./components/DeviceActionsCell.vue";
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

// ── View mode: table | cards ──
const viewMode = ref("table");

// ── KPI computed ──
const kpiStats = computed(() => {
  const devices = store.devices;
  return {
    online: devices.filter(d => d.status === "ONLINE").length,
    busy: devices.filter(d => d.status === "BUSY").length,
    offline: devices.filter(d => d.status === "OFFLINE" || d.status === "DISCONNECTED").length,
    total: devices.length,
  };
});

// ── Grouped devices for card view ──
const groupedDevices = computed(() => ({
  online: filteredDevices.value.filter(d => d.status === "ONLINE"),
  busy: filteredDevices.value.filter(d => d.status === "BUSY"),
  offline: filteredDevices.value.filter(d => d.status === "OFFLINE" || d.status === "DISCONNECTED"),
}));

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
  heartbeatTimer = setInterval(async () => {
    await store.doHeartbeat();
    loadDevices();
  }, 30000);
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

async function handleJoinQueue(device) {
  if (!currentUser) {
    ElMessage.warning("无法获取当前用户信息，请重新登录");
    return;
  }
  const result = await store.doJoinQueue(device.serial, currentUser);
  if (result.ok) {
    const pos = result.position || '?';
    ElMessage.success(`已加入 ${device.serial} 的等待队列，当前位置：第 ${pos} 位`);
  } else {
    ElMessage.error(result.error || "加入队列失败");
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
      icon="smartphone"
      icon-gradient="linear-gradient(135deg,#95D5B2,#52b788)"
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

        <!-- 操作栏：局域网连接 + 刷新设备 -->
        <div class="action-bar">
          <el-button class="action-bar-btn" size="small" @click="openNetworkDialog">
            <IconWifi :size="14" /> <span>局域网连接</span>
          </el-button>
          <el-button class="action-bar-btn" size="small" :loading="store.scanning || store.loading" @click="handleRefresh">
            <IconRefresh :size="14" /> <span>刷新设备</span>
          </el-button>
        </div>

        <!-- KPI 统计条 -->
        <div class="kpi-row">
          <div class="kpi-card"><div class="kpi-dot" style="background:#6BCB77"></div><div class="kpi-value">{{ kpiStats.online }}</div><div class="kpi-label">在线</div></div>
          <div class="kpi-card"><div class="kpi-dot" style="background:#FFB5A7"></div><div class="kpi-value">{{ kpiStats.busy }}</div><div class="kpi-label">使用中</div></div>
          <div class="kpi-card"><div class="kpi-dot" style="background:#d4d8dc"></div><div class="kpi-value">{{ kpiStats.offline }}</div><div class="kpi-label">离线</div></div>
          <div class="kpi-card"><div class="kpi-dot" style="background:var(--ink)"></div><div class="kpi-value">{{ kpiStats.total }}</div><div class="kpi-label">总计</div></div>
        </div>

        <!-- 筛选 + 视图切换 -->
        <div class="filter-bar">
          <DeviceFilterTabs :tabs="filterAppTabs" v-model="activeFilter" />
          <div class="view-toggle">
            <button class="view-btn" :class="{ active: viewMode === 'table' }" @click="viewMode = 'table'">📋 表格</button>
            <button class="view-btn" :class="{ active: viewMode === 'cards' }" @click="viewMode = 'cards'">📷 卡片</button>
          </div>
          <span class="filter-count">{{ filteredDevices.length }} 台设备</span>
        </div>

        <!-- 表视图：工具栏 + 表格 -->
        <template v-if="viewMode === 'table'">
          <div class="table-toolbar">
            <div class="page-size-control">
              <span class="toolbar-label">显示行数</span>
              <div class="page-size-btns">
                <button v-for="n in PAGE_SIZE_OPTIONS" :key="n" type="button" class="page-size-btn" :class="{ active: pageSize === n }" @click="setPageSize(n)">{{ n }}</button>
              </div>
            </div>
            <div v-if="filteredDevices.length > 0" class="table-toolbar-right">
              <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页 · 共 {{ filteredDevices.length }} 台</span>
              <div v-if="totalPages > 1" class="page-nav">
                <el-button class="wb-btn" size="small" :disabled="currentPage <= 1" @click="goPage(currentPage - 1)">上一页</el-button>
                <el-button class="wb-btn" size="small" :disabled="currentPage >= totalPages" @click="goPage(currentPage + 1)">下一页</el-button>
              </div>
            </div>
          </div>

        <!-- 表格视图 -->
        <el-card class="table-card" shadow="never">
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

                    <!-- Status cell -->
                    <template #cell-status="{ record }">
                      <DeviceStatusCell :device="record" :status-tag="statusTag" />
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

                    <!-- Actions cell -->
                    <template #cell-actions="{ record }">
                      <DeviceActionsCell
                        :device="record"
                        :current-user="currentUser"
                        @lock="handleLockClick"
                        @join-queue="handleJoinQueue"
                        @occupy="handleOccupyClick"
                        @disconnect="(d) => openDisconnectDialog(d.serial)"
                      />
                    </template>

                    <template #empty>
                      <EmptyState icon="📱"
                        :text="activeFilter === 'all' ? '暂无设备' : '没有匹配的设备'"
                        :hint="activeFilter === 'all' ? '点击「扫描设备」发现设备' : '尝试切换筛选条件'" />
                    </template>
              </AppTable>
          </div>
        </el-card>
        </template>

        <!-- 卡片视图：按状态分组 -->
        <div class="card-grid-grouped" v-if="viewMode === 'cards'">
          <div class="card-group" v-for="group in [
            { key:'online', label:'🟢 在线' },
            { key:'busy', label:'🔴 使用中' },
            { key:'offline', label:'⚫ 离线' }
          ]" :key="group.key">
            <template v-if="groupedDevices[group.key].length">
              <div class="card-group-title">
                {{ group.label }}
                <span class="card-group-count">{{ groupedDevices[group.key].length }}</span>
              </div>
              <div class="card-group-grid">
                <DeviceCard
                  v-for="dev in groupedDevices[group.key]"
                  :key="dev.serial"
                  :device="dev"
                  :status-tag="statusTag"
                  :display-model="displayModel"
                  :connection-label="connectionLabel"
                  :format-relative-time="formatRelativeTime"
                  :current-user="currentUser"
                  @click="handleRowClick"
                  @lock="handleLockClick"
                  @join-queue="handleJoinQueue"
                  @disconnect="(d) => openDisconnectDialog(d.serial)"
                />
              </div>
            </template>
          </div>
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
  background:
    radial-gradient(circle, #d4cdc0 0.8px, transparent 0.8px);
  background-size: 14px 14px;
  background-color: #fefcf6;
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
  padding: 16px 20px 20px;
  gap: 12px;
}

.doc-section__header {
  flex-shrink: 0;
  padding-bottom: 0;
}
.doc-section__title {
  font-family: 'Caveat', cursive;
  font-size: 20px; font-weight: 700; color: var(--ink);
}
.doc-section__title .doc-tag {
  font-size: 9px; padding: 1px 8px; border-radius: 4px 8px 4px 8px;
  background: #fff; color: #999; border: 1.5px solid #e8ecf1;
  font-weight: 700; margin-left: 8px;
}
.doc-section__label { color: #999; font-size: 10px; }

/* ── KPI 统计条 ── */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0;
  border: 2.5px solid var(--c-workflow);
  border-radius: 4px 8px 4px 8px;
  overflow: hidden;
  background: #fff;
  margin-bottom: 4px;
  flex-shrink: 0;
}
.kpi-card {
  padding: 12px 16px;
  text-align: center;
  border-right: 2px solid #e8ecf1;
}
.kpi-card:last-child { border-right: none; }
.kpi-dot {
  width: 8px; height: 8px; transform: rotate(45deg);
  margin: 0 auto 4px; border-radius: 1px;
}
.kpi-value {
  font-family: 'Caveat', 'Quicksand', cursive;
  font-size: 28px; font-weight: 700; color: var(--ink); line-height: 1;
}
.kpi-label {
  font-size: 9px; font-weight: 700; color: #999; margin-top: 2px;
  text-transform: uppercase; letter-spacing: 0.06em;
}

/* ── 视图切换 ── */
.view-toggle {
  display: flex; gap: 0;
  border: 2px solid var(--c-workflow); border-radius: 4px 8px 4px 8px;
  overflow: hidden;
}
.view-btn {
  padding: 5px 12px; font-size: 10px; font-weight: 700;
  background: #fff; color: #999; border: none;
  cursor: pointer; font-family: inherit; transition: all 0.12s;
  border-right: 1px solid #e8ecf1;
}
.view-btn:last-child { border-right: none; }
.view-btn.active { background: var(--c-workflow); color: #fff; }
.view-btn:hover:not(.active) { color: var(--c-workflow); }

/* ── 卡片分组视图 ── */
.card-grid-grouped {
  flex: 1; min-height: 0; overflow-y: auto;
  display: flex; flex-direction: column; gap: 16px;
  padding: 4px 0;
}
.card-group-title {
  font-family: 'Caveat', cursive; font-size: 18px; font-weight: 700;
  color: var(--ink); display: flex; align-items: center; gap: 8px;
  margin-bottom: 10px;
}
.card-group-title::after {
  content: ''; flex: 1; height: 2px; background: #e8ecf1; border-radius: 1px;
}
.card-group-count {
  font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #999;
  background: #f8f6f2; padding: 2px 8px; border-radius: 3px 6px 3px 6px;
  border: 1.5px solid #e8ecf1;
}
.card-group-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px;
}
@media (max-width: 900px) { .card-group-grid { grid-template-columns: repeat(2, 1fr); } }

/* ── 表格卡片 ── */
.filter-bar {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  flex-shrink: 0;
}
.filter-count {
  font-size: 12px; color: #999; font-weight: 600;
  white-space: nowrap; margin-left: auto;
}

/* ── 操作栏（局域网 + 刷新）── */
.action-bar {
  display: flex; align-items: center; gap: 8px; flex-shrink: 0;
}
.action-bar-btn {
  gap: 5px !important; padding: 5px 14px !important;
  border-radius: 4px 8px 4px 8px !important;
  border: 2px solid #6BCB77 !important;
  background: #fff !important; color: #2d7a2d !important;
  font-weight: 700 !important;
}
.action-bar-btn:hover { background: #C8F5D0 !important; }

/* ── 表格工具栏 ── */
.table-toolbar {
  display: flex; align-items: center; justify-content: space-between;
  gap: 10px; flex-wrap: wrap; padding: 0 0 10px; flex-shrink: 0;
}
.page-size-control { display: flex; align-items: center; gap: 8px; }
.toolbar-label { font-size: 11px; font-weight: 700; color: #999; white-space: nowrap; }
.page-size-btns { display: flex; gap: 6px; }
.page-size-btn {
  min-width: 40px;
  padding: 5px 10px;
  border-radius: 4px 8px 4px 8px;
  border: 2px solid #e8ecf1;
  background: #fff;
  color: #999;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: none;
  transition: all 0.15s;
}
.page-size-btn:hover { border-color: var(--c-workflow); color: var(--c-workflow); }
.page-size-btn.active {
  background: #E8F4FD;
  border-color: var(--c-workflow);
  color: var(--c-workflow);
}
.table-toolbar-right { display: flex; align-items: center; gap: 12px; margin-left: auto; flex-wrap: wrap; }
.page-info { font-size: 12px; color: #999; font-weight: 600; white-space: nowrap; }
.page-nav { display: flex; gap: 8px; }

/* ── 表格卡片 ── */
.table-card {
  flex: 1; min-height: 0; min-width: 0;
  display: flex; flex-direction: column; overflow: hidden;
  border-radius: 6px 10px 6px 10px;
  border: 2.5px solid var(--c-workflow);
  box-shadow: 2px 3px 0 rgba(137,207,240,0.12);
  background: #fff;
}
.table-card :deep(.el-card__body) {
  flex: 1; min-height: 0; display: flex; flex-direction: column;
  overflow: hidden; padding: 0;
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
  scrollbar-color: #d4cdc0 transparent;
}
.device-table-wrapper::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
.device-table-wrapper::-webkit-scrollbar-thumb {
  background: #d4cdc0;
  border-radius: 3px;
}
.device-table-wrapper :deep(.el-table),
.device-table-wrapper :deep(.el-table__body-wrapper) {
  overflow: visible !important;
  max-height: none !important;
}

/* ── 表头与正文颜色区分 + 行列线条 ── */
.device-table-wrapper :deep(.el-table th) {
  background: #f8f6f2 !important;
  color: var(--ink) !important;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.4px;
  border-right: 1px solid #e8ecf1 !important;
  border-bottom: 2px solid #e8ecf1 !important;
}
.device-table-wrapper :deep(.el-table td) {
  color: var(--ink);
  font-size: 13px;
  border-right: 1px solid #f0ede8 !important;
  border-bottom: 1px solid #f0ede8 !important;
}
.device-table-wrapper :deep(.el-table th:last-child),
.device-table-wrapper :deep(.el-table td:last-child) {
  border-right: none !important;
}

/* ── 操作列垂直居中 ── */
.device-table-wrapper :deep(.el-table td:last-child) {
  vertical-align: middle;
}
.device-table-wrapper :deep(.el-table td:last-child .cell) {
  display: flex;
  align-items: center;
  justify-content: center;
  padding-top: 8px;
  padding-bottom: 8px;
}

/* ── Row dot indicator ── */
.row-dot {
  color: var(--ink);
  font-size: 12px;
  line-height: 1;
  margin-right: 6px;
  vertical-align: middle;
}

/* ── Cell components (moved to DeviceStatusCell.vue / DeviceActionsCell.vue) ── */

/* ── Monospace serial text ── */
.mono-text {
  font-family: "Cascadia Code", "Fira Code", "Consolas", monospace;
  font-size: 13px;
  white-space: nowrap;
  vertical-align: middle;
}

/* ── Text helpers ── */
.text-muted { color: #999; font-size: 13px; }
.locked-by-text { color: #999; font-size: 13px; }
.last-seen-text { font-size: 13px; color: #999; }
.connection-text { font-size: 13px; color: var(--ink); font-weight: 600; white-space: nowrap; }

/* ── 操作按钮组（样式移至 DeviceActionsCell.vue）── */

/* ── Lock status badge ── */
.lock-badge {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 3px 6px 3px 6px;
  font-weight: 700;
  white-space: nowrap;
  display: inline-block;
}
.lock-badge--locked {
  background: #E8DDF8; color: #5a3fa0;
  border: 1.5px solid #A78BFA;
}
.lock-badge--shared {
  background: #C8F5D0; color: #2d7a2d;
  border: 1.5px solid #6BCB77;
}

/* ── Empty state ── */
.empty-state {
  color: #999;
  padding: 40px 0;
  text-align: center;
  font-size: 14px;
}

/* ── Row status styles — device table row highlighting ── */
:deep(.device-table-wrapper .el-table tbody tr[data-row-status="OFFLINE"]),
:deep(
  .device-table-wrapper .el-table tbody tr[data-row-status="DISCONNECTED"]
) {
  opacity: 0.5;
}
</style>
