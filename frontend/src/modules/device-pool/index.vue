<script setup>
/** Device Pool v2 — 设备管理主页面 per PRD-02 */
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
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
import { useDeviceActions } from "./composables/useDeviceActions.js";
import {
  PAGE_HEADER, FILTER_TABS, COLUMNS, EMPTY_TEXT,
  formatRelativeTime, displayModel, connectionLabel, statusTag,
} from "./constants.js";

const store = useDevicePoolStore();
const {
  disconnectDialog, networkDialog, currentUser,
  loadDevices, startHeartbeat, stopHeartbeat,
  handleRefresh, openNetworkDialog, handleNetworkConnect, cancelNetworkDialog,
  handleRowClick, handleLockClick, handleJoinQueue, handleCancelQueue,
  handleOccupyClick, handleRelease,
  openDisconnectDialog, handleDisconnectConfirm, cancelDisconnectDialog,
} = useDeviceActions(store);

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

// ── Helpers ──

function isRowSelected(record) {
  return record && record.serial === store.selectedSerial;
}

// ── Lifecycle ──

onMounted(() => {
  loadDevices();
  startHeartbeat();
});
onUnmounted(() => {
  stopHeartbeat();
});
</script>

<template>
  <div class="doc-page wb-shell device-workbench">
    <WorkbenchHeader
      :title="PAGE_HEADER.title"
      :subtitle="PAGE_HEADER.subtitle"
      :icon="PAGE_HEADER.icon"
      :icon-gradient="PAGE_HEADER.iconGradient"
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
          <div class="kpi-card"><div class="kpi-dot" style="background:var(--app-status-success)"></div><div class="kpi-value">{{ kpiStats.online }}</div><div class="kpi-label">在线</div></div>
          <div class="kpi-card"><div class="kpi-dot" style="background:var(--app-status-danger)"></div><div class="kpi-value">{{ kpiStats.busy }}</div><div class="kpi-label">使用中</div></div>
          <div class="kpi-card"><div class="kpi-dot" style="background:var(--app-offline)"></div><div class="kpi-value">{{ kpiStats.offline }}</div><div class="kpi-label">离线</div></div>
          <div class="kpi-card"><div class="kpi-dot" style="background:var(--app-ink)"></div><div class="kpi-value">{{ kpiStats.total }}</div><div class="kpi-label">总计</div></div>
        </div>

        <!-- 筛选 + 视图切换 -->
        <div class="filter-bar">
          <DeviceFilterTabs :tabs="FILTER_TABS" v-model="activeFilter" />
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
              :columns="COLUMNS"
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
                      <DeviceStatusCell :device="record" />
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

<style scoped src="./device-pool.css"></style>
